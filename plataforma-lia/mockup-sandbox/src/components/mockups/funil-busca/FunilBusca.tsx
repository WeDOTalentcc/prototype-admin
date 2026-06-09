import React, { useState } from "react"
import {
  Search, Plus, ArrowLeft, SlidersHorizontal, Columns3,
  Star, Pin, CheckSquare, Square, Linkedin, Mail, Phone,
  CheckCircle2, AlertTriangle, CreditCard, Loader2, Check,
  X, ChevronUp, ChevronDown, ChevronRight, Edit2
} from "lucide-react"

// ---------------------------------------------------------------------------
// Token map (mirrors JDScoresComparison pattern):
//   lia-bg-primary       → white      lia-bg-secondary  → slate-50
//   lia-bg-tertiary      → slate-100  lia-text-primary  → slate-900
//   lia-text-secondary   → slate-600  lia-text-tertiary → slate-500
//   lia-border-subtle    → slate-200  status-success    → emerald-600
//   status-warning       → amber-600  lia-btn-primary   → indigo-600
//   text-micro           → text-[11px] text-base-ui     → text-sm
// ---------------------------------------------------------------------------

function cn(...inputs: Array<string | false | null | undefined>): string {
  return inputs.filter(Boolean).join(" ")
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface Candidate {
  id: string
  name: string
  avatar?: string
  initials: string
  current_title: string
  current_company: string
  salary: string
  salary_expectation: string
  email?: string
  phone?: string
  has_email: boolean
  has_phone: boolean
  email_valid?: boolean
  phone_valid?: boolean
  source: "global" | "local"
}

type RevealedContacts = Record<string, { email?: string; phone?: string }>

// ---------------------------------------------------------------------------
// Dataset — mirrors screenshot exactly
// ---------------------------------------------------------------------------
const CANDIDATES: Candidate[] = [
  { id: "c1", name: "Maria Santos", initials: "MS", current_title: "UX Designer Pleno", current_company: "DesignStudio", salary: "N/A", salary_expectation: "N/A", email: "maria.santos.eval@email.com", phone: "+55 11 95678-9012", has_email: true, has_phone: true, email_valid: true, phone_valid: true, source: "global" },
  { id: "c2", name: "Ana Almeida", initials: "AA", current_title: "UX Designer", current_company: "CI&T", salary: "N/A", salary_expectation: "N/A", email: "ana.almeida24@email.com", phone: "+55 11 92441-2559", has_email: true, has_phone: true, email_valid: true, phone_valid: true, source: "global" },
  { id: "c3", name: "Fernanda Ribeiro", initials: "FR", current_title: "UX Designer", current_company: "Creditas", salary: "N/A", salary_expectation: "N/A", has_email: true, has_phone: true, source: "global" },
  { id: "c4", name: "Rafael Costa", initials: "RC", current_title: "Tech Lead Backend", current_company: "InfrasTech", salary: "N/A", salary_expectation: "N/A", has_email: true, has_phone: true, source: "global" },
  { id: "c5", name: "Bruna Moura", initials: "BM", current_title: "Tech Lead", current_company: "Hotmart", salary: "N/A", salary_expectation: "N/A", email: "bruna.moura45@email.com", phone: "+55 11 94147-9660", has_email: true, has_phone: true, email_valid: true, phone_valid: true, source: "global" },
  { id: "c6", name: "Beatriz Silva", initials: "BS", current_title: "Tech Lead", current_company: "Boticário", salary: "N/A", salary_expectation: "N/A", email: "beatriz.silva7@email.com", phone: "+55 11 91810-8585", has_email: true, has_phone: true, email_valid: false, phone_valid: true, source: "global" },
  { id: "c7", name: "Ana Araújo", initials: "AA", current_title: "Tech Lead", current_company: "B3", salary: "N/A", salary_expectation: "N/A", has_email: true, has_phone: true, source: "global" },
  { id: "c8", name: "Isabela Moura", initials: "IM", current_title: "Tech Lead", current_company: "IBM Brasil", salary: "N/A", salary_expectation: "N/A", email: "isabela.moura55@email.com", has_email: true, has_phone: true, phone_valid: true, source: "global" },
  { id: "c9", name: "Fabiana Moura", initials: "FM", current_title: "Software Engineer", current_company: "B3", salary: "N/A", salary_expectation: "N/A", email: "fabiana.moura9@email.com", phone: "+55 11 93252-3127", has_email: true, has_phone: true, email_valid: true, phone_valid: true, source: "global" },
  { id: "c10", name: "Tatiana Rocha", initials: "TR", current_title: "Software Engineer", current_company: "Accenture Brasil", salary: "N/A", salary_expectation: "N/A", email: "tatiana.rocha8@email.com", phone: "+55 11 92660-4125", has_email: true, has_phone: true, email_valid: true, phone_valid: false, source: "global" },
]

// ---------------------------------------------------------------------------
// ValidityBadge
// ---------------------------------------------------------------------------
function ValidityBadge({ valid, label, badLabel }: { valid?: boolean; label: string; badLabel: string }) {
  if (valid === true) return <CheckCircle2 className="w-3 h-3 shrink-0 text-emerald-600" title={label} />
  if (valid === false) return <AlertTriangle className="w-3 h-3 shrink-0 text-amber-500" title={badLabel} />
  return null
}

// ---------------------------------------------------------------------------
// EmailCell
// ---------------------------------------------------------------------------
function EmailCell({ candidate, revealed, onReveal }: {
  candidate: Candidate
  revealed: RevealedContacts
  onReveal: (c: Candidate, t: "email" | "phone") => void
}) {
  const email = revealed[candidate.id]?.email || candidate.email
  if (email) {
    return (
      <span className="inline-flex items-center gap-1 min-w-0">
        <span className="text-xs text-slate-900 truncate max-w-[160px]">{email}</span>
        <ValidityBadge valid={candidate.email_valid} label="E-mail verificado" badLabel="E-mail não verificado" />
      </span>
    )
  }
  if (candidate.has_email && candidate.source === "global") {
    return (
      <button
        onClick={(e) => { e.stopPropagation(); onReveal(candidate, "email") }}
        className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-medium rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors"
        title="Clique para revelar email"
      >
        <Mail className="w-3 h-3" />
        <span>Revelar</span>
      </button>
    )
  }
  return <span className="text-xs text-slate-900">-</span>
}

// ---------------------------------------------------------------------------
// PhoneCell
// ---------------------------------------------------------------------------
function PhoneCell({ candidate, revealed, onReveal }: {
  candidate: Candidate
  revealed: RevealedContacts
  onReveal: (c: Candidate, t: "email" | "phone") => void
}) {
  const phone = revealed[candidate.id]?.phone || candidate.phone
  if (phone) {
    return (
      <span className="inline-flex items-center gap-1 min-w-0">
        <span className="text-xs text-slate-900">{phone}</span>
        <ValidityBadge valid={candidate.phone_valid} label="Telefone válido" badLabel="Telefone inválido" />
      </span>
    )
  }
  if (candidate.has_phone && candidate.source === "global") {
    return (
      <button
        onClick={(e) => { e.stopPropagation(); onReveal(candidate, "phone") }}
        className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-medium rounded-full bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors"
        title="Clique para revelar celular"
      >
        <Phone className="w-3 h-3" />
        <span>Revelar</span>
      </button>
    )
  }
  return <span className="text-xs text-slate-900">-</span>
}

// ---------------------------------------------------------------------------
// RevealCreditsModal — replica fiel de reveal-credits-modal.tsx
// ---------------------------------------------------------------------------
function RevealCreditsModal({ isOpen, onClose, onConfirm, revealType, candidateName }: {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  revealType: "email" | "phone"
  candidateName: string
}) {
  const [loading, setLoading] = useState(false)
  if (!isOpen) return null

  const credits = revealType === "email" ? 2 : 14
  const Icon = revealType === "email" ? Mail : Phone
  const label = revealType === "email" ? "email" : "telefone"

  const handleConfirm = () => {
    setLoading(true)
    setTimeout(() => { setLoading(false); onConfirm() }, 900)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="w-full max-w-md bg-white rounded-xl border border-slate-200 shadow-xl p-6 space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-slate-100 text-slate-600">
            <Icon className="w-5 h-5" />
          </div>
          <h2 className="text-sm font-semibold text-slate-900">Revelar {label}</h2>
        </div>

        {/* Body */}
        <p className="text-sm text-slate-600">
          Deseja revelar o {label} de{" "}
          <strong className="text-slate-900">{candidateName}</strong>?
        </p>

        {/* Cost warning */}
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
          <div className="flex items-start gap-3">
            <CreditCard className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <p className="font-semibold text-amber-700">Custo: {credits} créditos</p>
              <p className="text-sm text-amber-600 mt-1">
                {revealType === "email"
                  ? "O custo será cobrado apenas se o candidato tiver email disponível."
                  : "O custo será cobrado apenas se o candidato tiver telefone disponível."}
              </p>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="flex items-start gap-2 text-xs text-slate-500">
          <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>Esta ação consumirá créditos da sua conta.</span>
        </div>

        {/* Buttons */}
        <div className="flex justify-end gap-2 pt-1">
          <button
            onClick={onClose}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            <X className="w-4 h-4" /> Cancelar
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-70"
          >
            {loading
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Revelando...</>
              : <><Check className="w-4 h-4" /> Confirmar ({credits} créditos)</>
            }
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// BulkRevealModal — replica fiel de BulkRevealModal.tsx
// ---------------------------------------------------------------------------
function BulkRevealModal({ isOpen, onClose, count }: { isOpen: boolean; onClose: () => void; count: number }) {
  const [revealEmail, setRevealEmail] = useState(true)
  const [revealPhone, setRevealPhone] = useState(false)
  const [loading, setLoading] = useState(false)
  if (!isOpen) return null

  const maxCredits = count * ((revealEmail ? 2 : 0) + (revealPhone ? 14 : 0))

  const handleConfirm = () => {
    setLoading(true)
    setTimeout(() => { setLoading(false); onClose() }, 1200)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="w-full max-w-md bg-white rounded-xl border border-slate-200 shadow-xl p-6 space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-sm font-semibold text-slate-900">
          Revelar contatos de {count} candidato{count !== 1 ? "s" : ""}
        </h2>
        <p className="text-sm text-slate-600">
          Escolha o que revelar. A cobrança ocorre apenas pelos contatos efetivamente disponíveis.
        </p>

        <div className="space-y-2">
          <label className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50">
            <input type="checkbox" checked={revealEmail} onChange={e => setRevealEmail(e.target.checked)} className="w-4 h-4 accent-indigo-600" />
            <Mail className="w-4 h-4 text-slate-600" />
            <span className="flex-1 text-sm text-slate-900">Email</span>
            <span className="text-xs text-slate-500">2 créd./candidato</span>
          </label>
          <label className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 cursor-pointer hover:bg-slate-50">
            <input type="checkbox" checked={revealPhone} onChange={e => setRevealPhone(e.target.checked)} className="w-4 h-4 accent-indigo-600" />
            <Phone className="w-4 h-4 text-slate-600" />
            <span className="flex-1 text-sm text-slate-900">Telefone</span>
            <span className="text-xs text-slate-500">14 créd./candidato</span>
          </label>
        </div>

        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3">
          <CreditCard className="w-5 h-5 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold text-amber-700">Custo máximo: {maxCredits} créditos</p>
            <p className="text-sm text-amber-600 mt-1">Candidatos sem o contato escolhido não consomem créditos.</p>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} disabled={loading} className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50">
            Cancelar
          </button>
          <button onClick={handleConfirm} disabled={loading || (!revealEmail && !revealPhone)} className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-70">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Revelando…</> : `Revelar (${count})`}
          </button>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export default function FunilBusca() {
  const [activeTab, setActiveTab] = useState<string>("busca")
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [revealedContacts, setRevealedContacts] = useState<RevealedContacts>({
    c1: { email: "maria.santos.eval@email.com", phone: "+55 11 95678-9012" },
    c2: { email: "ana.almeida24@email.com", phone: "+55 11 92441-2559" },
    c5: { email: "bruna.moura45@email.com", phone: "+55 11 94147-9660" },
    c6: { email: "beatriz.silva7@email.com", phone: "+55 11 91810-8585" },
    c9: { email: "fabiana.moura9@email.com", phone: "+55 11 93252-3127" },
    c10: { email: "tatiana.rocha8@email.com", phone: "+55 11 92660-4125" },
  })

  // Single reveal modal
  const [revealModal, setRevealModal] = useState<{ open: boolean; candidate: Candidate | null; type: "email" | "phone" }>({ open: false, candidate: null, type: "email" })
  // Bulk reveal modal
  const [bulkModal, setBulkModal] = useState(false)

  const openReveal = (candidate: Candidate, type: "email" | "phone") => {
    setRevealModal({ open: true, candidate, type })
  }

  const confirmReveal = () => {
    if (!revealModal.candidate) return
    const fakeEmail = `${revealModal.candidate.name.toLowerCase().replace(/\s+/g, ".")}@email.com`
    const fakePhone = `+55 11 9${Math.floor(Math.random() * 9000 + 1000)}-${Math.floor(Math.random() * 9000 + 1000)}`
    setRevealedContacts(prev => ({
      ...prev,
      [revealModal.candidate!.id]: {
        ...prev[revealModal.candidate!.id],
        [revealModal.type]: revealModal.type === "email" ? fakeEmail : fakePhone,
      }
    }))
    setRevealModal({ open: false, candidate: null, type: "email" })
  }

  const toggleAll = () => {
    if (selected.size === CANDIDATES.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(CANDIDATES.map(c => c.id)))
    }
  }

  const toggleOne = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const allSelected = selected.size === CANDIDATES.length
  const someSelected = selected.size > 0 && selected.size < CANDIDATES.length

  const tabs = ["Busca", "Favoritos", "Listas", "Bancos de Talentos", "Buscas Salvas", "Histórico"]

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      {/* ── Page header ── */}
      <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900">Funil de Talentos</h1>
        <div className="flex items-center gap-2">
          <button className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700">
            <Plus className="w-4 h-4" /> Novo Candidato
          </button>
          <button className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50">
            <Search className="w-4 h-4" /> Nova Busca
          </button>
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="bg-white border-b border-slate-200 px-6">
        <div className="flex gap-0">
          {tabs.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab.toLowerCase())}
              className={cn(
                "px-4 py-3 text-sm font-medium border-b-2 transition-colors",
                activeTab === tab.toLowerCase()
                  ? "border-indigo-600 text-indigo-700"
                  : "border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300"
              )}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* ── Content ── */}
      <div className="p-4 flex flex-col gap-3">

        {/* Search bar row */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <button className="p-1 rounded hover:bg-slate-100">
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-md px-3 py-1.5">
              <Search className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-700 font-medium">Busca realizada</span>
              <button className="p-0.5 rounded hover:bg-slate-100 ml-0.5">
                <Edit2 className="w-3 h-3 text-slate-400" />
              </button>
            </div>
            <button className="flex items-center gap-1 text-indigo-600 hover:text-indigo-700 text-sm font-medium">
              Editar Filtros <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={toggleAll}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
            >
              {allSelected
                ? <CheckSquare className="w-4 h-4 text-indigo-600" />
                : <Square className="w-4 h-4" />
              }
              Selecionar Todos
            </button>
            <button className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50">
              <SlidersHorizontal className="w-4 h-4" /> Filtros
            </button>
            <button className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md border border-slate-300 bg-white text-slate-700 hover:bg-slate-50">
              <Columns3 className="w-4 h-4" /> Colunas <span className="ml-1 text-xs bg-slate-100 px-1.5 py-0.5 rounded-full font-medium">11</span>
            </button>
          </div>
        </div>

        {/* Bulk actions bar (visible when candidates selected) */}
        {selected.size > 0 && (
          <div className="flex items-center gap-2 px-4 py-2.5 bg-indigo-50 border border-indigo-200 rounded-lg text-sm text-indigo-700 font-medium">
            <span>{selected.size} candidato{selected.size !== 1 ? "s" : ""} selecionado{selected.size !== 1 ? "s" : ""}</span>
            <div className="flex-1" />
            <button
              onClick={() => setBulkModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] rounded-md bg-indigo-600 text-white hover:bg-indigo-700"
            >
              <Mail className="w-3.5 h-3.5" /> Revelar Contatos
            </button>
            <button className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] rounded-md border border-indigo-300 bg-white text-indigo-700 hover:bg-indigo-50">
              <X className="w-3.5 h-3.5" /> Deselecionar
            </button>
          </div>
        )}

        {/* Table */}
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="w-10 px-3 py-3">
                    <button onClick={toggleAll} className="flex items-center">
                      {allSelected
                        ? <CheckSquare className="w-4 h-4 text-indigo-600" />
                        : someSelected
                          ? <div className="w-4 h-4 rounded border-2 border-indigo-500 bg-indigo-100 flex items-center justify-center"><div className="w-1.5 h-0.5 bg-indigo-600" /></div>
                          : <Square className="w-4 h-4 text-slate-400" />
                      }
                    </button>
                  </th>
                  <th className="w-8 px-1 py-3"></th>
                  <th className="w-8 px-1 py-3"></th>
                  <th className="px-3 py-3 text-left">
                    <div className="flex items-center gap-1 text-xs font-semibold text-slate-500 uppercase tracking-wide cursor-pointer hover:text-slate-700">
                      Cargo atual <ChevronUp className="w-3 h-3 opacity-50" />
                    </div>
                  </th>
                  <th className="px-3 py-3 text-left">
                    <div className="flex items-center gap-1 text-xs font-semibold text-slate-500 uppercase tracking-wide cursor-pointer hover:text-slate-700">
                      Empresa atual <ChevronUp className="w-3 h-3 opacity-50" />
                    </div>
                  </th>
                  <th className="px-3 py-3 text-left">
                    <div className="flex items-center gap-1 text-xs font-semibold text-slate-500 uppercase tracking-wide cursor-pointer hover:text-slate-700">
                      Salário atual <ChevronUp className="w-3 h-3 opacity-50" />
                    </div>
                  </th>
                  <th className="px-3 py-3 text-left">
                    <div className="flex items-center gap-1 text-xs font-semibold text-slate-500 uppercase tracking-wide cursor-pointer hover:text-slate-700">
                      Expectativa salarial <ChevronUp className="w-3 h-3 opacity-50" />
                    </div>
                  </th>
                  <th className="px-3 py-3 text-left min-w-[200px]">
                    <div className="flex items-center gap-1 text-xs font-semibold text-slate-500 uppercase tracking-wide cursor-pointer hover:text-slate-700">
                      E-mail <ChevronUp className="w-3 h-3 opacity-50" />
                    </div>
                  </th>
                  <th className="px-3 py-3 text-left min-w-[180px]">
                    <div className="flex items-center gap-1 text-xs font-semibold text-slate-500 uppercase tracking-wide cursor-pointer hover:text-slate-700">
                      Celular <ChevronUp className="w-3 h-3 opacity-50" />
                    </div>
                  </th>
                  <th className="px-3 py-3 text-left w-16">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">LinkedIn</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {CANDIDATES.map((c, idx) => {
                  const isSelected = selected.has(c.id)
                  return (
                    <tr
                      key={c.id}
                      className={cn(
                        "border-b border-slate-100 hover:bg-slate-50 transition-colors cursor-pointer",
                        isSelected && "bg-indigo-50/50",
                        idx === CANDIDATES.length - 1 && "border-b-0"
                      )}
                    >
                      {/* Checkbox */}
                      <td className="px-3 py-3" onClick={(e) => { e.stopPropagation(); toggleOne(c.id) }}>
                        {isSelected
                          ? <CheckSquare className="w-4 h-4 text-indigo-600" />
                          : <Square className="w-4 h-4 text-slate-300 hover:text-slate-500" />
                        }
                      </td>

                      {/* Star */}
                      <td className="px-1 py-3">
                        <button className="text-slate-300 hover:text-amber-400 transition-colors">
                          <Star className="w-4 h-4" />
                        </button>
                      </td>

                      {/* Pin */}
                      <td className="px-1 py-3">
                        <button className="text-slate-300 hover:text-slate-600 transition-colors">
                          <Pin className="w-4 h-4" />
                        </button>
                      </td>

                      {/* Candidate name (not shown in screenshot but table structure has it — we skip to cargo) */}
                      <td className="px-3 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-[10px] font-semibold shrink-0">
                            {c.initials}
                          </div>
                          <div className="min-w-0">
                            <div className="text-xs font-medium text-slate-900 truncate">{c.current_title}</div>
                            <div className="text-[10px] text-slate-500 truncate">{c.name}</div>
                          </div>
                        </div>
                      </td>

                      {/* Company */}
                      <td className="px-3 py-3">
                        <span className="text-xs text-slate-700">{c.current_company}</span>
                      </td>

                      {/* Salary */}
                      <td className="px-3 py-3">
                        <span className="text-xs text-slate-500">{c.salary}</span>
                      </td>

                      {/* Salary expectation */}
                      <td className="px-3 py-3">
                        <span className="text-xs text-slate-500">{c.salary_expectation}</span>
                      </td>

                      {/* Email */}
                      <td className="px-3 py-3">
                        <EmailCell candidate={c} revealed={revealedContacts} onReveal={openReveal} />
                      </td>

                      {/* Phone */}
                      <td className="px-3 py-3">
                        <PhoneCell candidate={c} revealed={revealedContacts} onReveal={openReveal} />
                      </td>

                      {/* LinkedIn */}
                      <td className="px-3 py-3">
                        <button className="inline-flex items-center justify-center w-7 h-7 rounded-md hover:bg-slate-100 transition-colors text-slate-400 hover:text-indigo-600">
                          <Linkedin className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 bg-slate-50/60 text-xs text-slate-500">
            <span>Exibindo {CANDIDATES.length} de 127 resultados</span>
            <button className="px-3 py-1.5 rounded-md border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 text-xs font-medium">
              Carregar mais
            </button>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-6 text-[11px] text-slate-500 px-1">
          <div className="flex items-center gap-1.5">
            <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              <Mail className="w-3 h-3" />
              <span>Revelar</span>
            </div>
            <span>= contato disponível, clique para consumir créditos e revelar</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
              <Phone className="w-3 h-3" />
              <span>Revelar</span>
            </div>
            <span>= celular disponível (14 créditos)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>= contato verificado</span>
          </div>
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
            <span>= dado com ressalva</span>
          </div>
        </div>
      </div>

      {/* Modals */}
      <RevealCreditsModal
        isOpen={revealModal.open}
        onClose={() => setRevealModal(prev => ({ ...prev, open: false }))}
        onConfirm={confirmReveal}
        revealType={revealModal.type}
        candidateName={revealModal.candidate?.name ?? ""}
      />
      <BulkRevealModal
        isOpen={bulkModal}
        onClose={() => setBulkModal(false)}
        count={selected.size}
      />
    </div>
  )
}
