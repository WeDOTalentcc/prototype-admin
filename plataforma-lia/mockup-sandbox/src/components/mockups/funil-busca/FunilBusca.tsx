/**
 * FunilBusca — Funil de Talentos: Resultado de Busca
 * Mockup 100% fiel ao sistema real.
 *
 * Tokens usados literalmente (do design-tokens.css + tailwind.config.ts):
 *   lia-bg-primary       #FFFFFF     lia-bg-secondary   #F9FAFB
 *   lia-bg-tertiary      #F3F4F6     lia-text-primary   #111111
 *   lia-text-secondary   #2D2D2D     lia-text-tertiary  #5C5C5C
 *   lia-text-disabled    #999999     lia-border-subtle  #D4D4D4
 *   lia-border-default   #BEBEBE     lia-interactive-hover #F3F4F6
 *   lia-interactive-active #E5E7EB   lia-btn-primary-bg #111827
 *   lia-btn-primary-text #FFFFFF     lia-btn-primary-hover #000000
 *   status-success       #16A34A     status-success/10  rgba(22,163,74,.10)
 *   status-success/15    rgba(22,163,74,.15)
 *   status-warning       #D97706     status-warning/10  rgba(217,119,6,.10)
 *   status-warning/30    rgba(217,119,6,.30)
 *   Fonte: Open Sans (font-sans, 85%) + Inter (font-data, números)
 *   Tabs: pill-style — active bg #FFFFFF shadow, container bg #F9FAFB
 */

import React, { useState } from "react"
import {
  Search, Plus, ArrowLeft, SlidersHorizontal, Columns3,
  Star, Pin, CheckSquare, Square, Linkedin, Mail, Phone,
  CheckCircle2, AlertTriangle, CreditCard, Loader2, Check,
  X, ChevronUp, ChevronRight, Edit2
} from "lucide-react"

// ─── Inline style tokens (exact values from design-tokens.css) ────────────
const T = {
  bgPrimary:          "#FFFFFF",
  bgSecondary:        "#F9FAFB",
  bgTertiary:         "#F3F4F6",
  textPrimary:        "#111111",
  textSecondary:      "#2D2D2D",
  textTertiary:       "#5C5C5C",
  textDisabled:       "#999999",
  borderSubtle:       "#D4D4D4",
  borderDefault:      "#BEBEBE",
  interactiveHover:   "#F3F4F6",
  interactiveActive:  "#E5E7EB",
  btnPrimaryBg:       "#111827",
  btnPrimaryHover:    "#000000",
  btnPrimaryText:     "#FFFFFF",
  success:            "#16A34A",
  successBg10:        "rgba(22,163,74,.10)",
  successBg15:        "rgba(22,163,74,.15)",
  warning:            "#D97706",
  warningBg10:        "rgba(217,119,6,.10)",
  warningBorder30:    "rgba(217,119,6,.30)",
  shadowSm:           "0 1px 2px 0 rgb(0 0 0 / .05)",
  shadowMd:           "0 4px 6px -1px rgb(0 0 0 / .08)",
}

const FONTS = {
  sans:   "'Open Sans', system-ui, sans-serif",
  data:   "'Inter', system-ui, sans-serif",
}

// ─── Types ───────────────────────────────────────────────────────────────
interface Candidate {
  id: string
  name: string
  initials: string
  current_title: string
  current_company: string
  email?: string
  phone?: string
  has_email: boolean
  has_phone: boolean
  email_valid?: boolean | null
  phone_valid?: boolean | null
  source: "global" | "local"
}

type RevealedContacts = Record<string, { email?: string; phone?: string }>

// ─── Dataset ─────────────────────────────────────────────────────────────
const CANDIDATES: Candidate[] = [
  { id:"c1",  name:"Maria Santos",    initials:"MS", current_title:"UX Designer Pleno",    current_company:"DesignStudio",    email:"maria.santos.eval@email.com", phone:"+55 11 95678-9012", has_email:true, has_phone:true, email_valid:true,  phone_valid:true,  source:"global" },
  { id:"c2",  name:"Ana Almeida",     initials:"AA", current_title:"UX Designer",           current_company:"CI&T",            email:"ana.almeida24@email.com",     phone:"+55 11 92441-2559", has_email:true, has_phone:true, email_valid:true,  phone_valid:true,  source:"global" },
  { id:"c3",  name:"Fernanda Ribeiro",initials:"FR", current_title:"UX Designer",           current_company:"Creditas",        has_email:true, has_phone:true, source:"global" },
  { id:"c4",  name:"Rafael Costa",    initials:"RC", current_title:"Tech Lead Backend",     current_company:"InfrasTech",      has_email:true, has_phone:true, source:"global" },
  { id:"c5",  name:"Bruna Moura",     initials:"BM", current_title:"Tech Lead",             current_company:"Hotmart",         email:"bruna.moura45@email.com",     phone:"+55 11 94147-9660", has_email:true, has_phone:true, email_valid:true,  phone_valid:true,  source:"global" },
  { id:"c6",  name:"Beatriz Silva",   initials:"BS", current_title:"Tech Lead",             current_company:"Boticário",       email:"beatriz.silva7@email.com",    phone:"+55 11 91810-8585", has_email:true, has_phone:true, email_valid:false, phone_valid:true,  source:"global" },
  { id:"c7",  name:"Ana Araújo",      initials:"AA", current_title:"Tech Lead",             current_company:"B3",              has_email:true, has_phone:true, source:"global" },
  { id:"c8",  name:"Isabela Moura",   initials:"IM", current_title:"Tech Lead",             current_company:"IBM Brasil",      email:"isabela.moura55@email.com",   has_email:true, has_phone:true, phone_valid:true,  source:"global" },
  { id:"c9",  name:"Fabiana Moura",   initials:"FM", current_title:"Software Engineer",     current_company:"B3",              email:"fabiana.moura9@email.com",    phone:"+55 11 93252-3127", has_email:true, has_phone:true, email_valid:true,  phone_valid:true,  source:"global" },
  { id:"c10", name:"Tatiana Rocha",   initials:"TR", current_title:"Software Engineer",     current_company:"Accenture Brasil",email:"tatiana.rocha8@email.com",   phone:"+55 11 92660-4125", has_email:true, has_phone:true, email_valid:true,  phone_valid:false, source:"global" },
]

// ─── ValidityBadge ───────────────────────────────────────────────────────
function ValidityBadge({ valid }: { valid?: boolean | null }) {
  if (valid === true)  return <CheckCircle2  style={{ width:12, height:12, flexShrink:0, color:T.success }}  />
  if (valid === false) return <AlertTriangle style={{ width:12, height:12, flexShrink:0, color:T.warning }}  />
  return null
}

// ─── EmailCell — mirrors renderEmailCell exactly ──────────────────────────
function EmailCell({ candidate, revealed, onReveal }: {
  candidate: Candidate
  revealed: RevealedContacts
  onReveal: (c: Candidate, t: "email"|"phone") => void
}) {
  const email = revealed[candidate.id]?.email || candidate.email
  if (email) {
    return (
      <span style={{ display:"inline-flex", alignItems:"center", gap:4, minWidth:0 }}>
        <span style={{ fontFamily:FONTS.sans, fontSize:12, color:T.textPrimary, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{email}</span>
        <ValidityBadge valid={candidate.email_valid} />
      </span>
    )
  }
  if (candidate.has_email && candidate.source === "global") {
    return (
      <button
        onClick={e => { e.stopPropagation(); onReveal(candidate, "email") }}
        style={{
          display:"inline-flex", alignItems:"center", gap:6,
          padding:"2px 8px", fontSize:11, fontWeight:500,
          fontFamily:FONTS.sans,
          borderRadius:9999, border:"none", cursor:"pointer",
          background:T.bgTertiary, color:T.textSecondary,
        }}
        onMouseEnter={e => (e.currentTarget.style.background = T.interactiveActive)}
        onMouseLeave={e => (e.currentTarget.style.background = T.bgTertiary)}
      >
        <Mail style={{ width:12, height:12 }} />
        <span>Revelar</span>
      </button>
    )
  }
  return <span style={{ fontSize:12, color:T.textPrimary }}>-</span>
}

// ─── PhoneCell — mirrors renderPhoneCell exactly ──────────────────────────
function PhoneCell({ candidate, revealed, onReveal }: {
  candidate: Candidate
  revealed: RevealedContacts
  onReveal: (c: Candidate, t: "email"|"phone") => void
}) {
  const phone = revealed[candidate.id]?.phone || candidate.phone
  if (phone) {
    return (
      <span style={{ display:"inline-flex", alignItems:"center", gap:4 }}>
        <span style={{ fontFamily:FONTS.data, fontSize:12, color:T.textPrimary }}>{phone}</span>
        <ValidityBadge valid={candidate.phone_valid} />
      </span>
    )
  }
  if (candidate.has_phone && candidate.source === "global") {
    return (
      <button
        onClick={e => { e.stopPropagation(); onReveal(candidate, "phone") }}
        style={{
          display:"inline-flex", alignItems:"center", gap:6,
          padding:"2px 8px", fontSize:11, fontWeight:500,
          fontFamily:FONTS.sans,
          borderRadius:9999, border:"none", cursor:"pointer",
          background:T.successBg10, color:T.success,
        }}
        onMouseEnter={e => (e.currentTarget.style.background = T.successBg15)}
        onMouseLeave={e => (e.currentTarget.style.background = T.successBg10)}
      >
        <Phone style={{ width:12, height:12 }} />
        <span>Revelar</span>
      </button>
    )
  }
  return <span style={{ fontSize:12, color:T.textPrimary }}>-</span>
}

// ─── RevealCreditsModal — mirrors reveal-credits-modal.tsx exactly ────────
function RevealCreditsModal({ isOpen, onClose, onConfirm, revealType, candidateName }: {
  isOpen: boolean; onClose: () => void; onConfirm: () => void
  revealType: "email"|"phone"; candidateName: string
}) {
  const [loading, setLoading] = useState(false)
  if (!isOpen) return null
  const credits = revealType === "email" ? 2 : 14
  const Icon    = revealType === "email" ? Mail : Phone
  const label   = revealType === "email" ? "email" : "celular"

  const handleConfirm = () => {
    setLoading(true)
    setTimeout(() => { setLoading(false); onConfirm() }, 900)
  }

  return (
    <div
      onClick={onClose}
      style={{
        position:"fixed", inset:0, zIndex:50,
        display:"flex", alignItems:"center", justifyContent:"center",
        background:"rgba(0,0,0,.6)", padding:16,
        fontFamily:FONTS.sans,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width:"100%", maxWidth:420,
          background:T.bgPrimary,
          borderRadius:12, border:`1px solid ${T.borderSubtle}`,
          boxShadow:T.shadowMd,
          padding:24, display:"flex", flexDirection:"column", gap:20,
        }}
      >
        {/* Header */}
        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
          <div style={{ padding:10, borderRadius:12, background:T.bgTertiary, color:T.textSecondary }}>
            <Icon style={{ width:20, height:20 }} />
          </div>
          <span style={{ fontSize:14, fontWeight:600, color:T.textPrimary }}>Revelar {label}</span>
        </div>

        {/* Body */}
        <p style={{ fontSize:14, color:T.textSecondary, margin:0 }}>
          Deseja revelar o {label} de <strong style={{ color:T.textPrimary }}>{candidateName}</strong>?
        </p>

        {/* Cost box — mirrors status-warning/10 bg + status-warning/30 border */}
        <div style={{ padding:16, borderRadius:12, background:T.warningBg10, border:`1px solid ${T.warningBorder30}` }}>
          <div style={{ display:"flex", gap:12, alignItems:"flex-start" }}>
            <CreditCard style={{ width:20, height:20, color:T.warning, flexShrink:0, marginTop:1 }} />
            <div>
              <p style={{ fontWeight:600, color:T.warning, fontSize:14, margin:"0 0 4px" }}>Custo: {credits} créditos</p>
              <p style={{ fontSize:13, color:T.warning, margin:0, opacity:.85 }}>
                {revealType === "email"
                  ? "O custo será cobrado apenas se o candidato tiver email disponível."
                  : "O custo será cobrado apenas se o candidato tiver telefone disponível."}
              </p>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <div style={{ display:"flex", gap:6, alignItems:"flex-start" }}>
          <AlertTriangle style={{ width:14, height:14, color:T.textTertiary, flexShrink:0, marginTop:1 }} />
          <span style={{ fontSize:12, color:T.textTertiary }}>Esta ação consumirá créditos da sua conta.</span>
        </div>

        {/* Actions */}
        <div style={{ display:"flex", justifyContent:"flex-end", gap:8 }}>
          <button
            onClick={onClose} disabled={loading}
            style={{
              display:"inline-flex", alignItems:"center", gap:8,
              padding:"8px 14px", fontSize:13, fontWeight:500, borderRadius:6, cursor:"pointer",
              background:T.bgPrimary, color:T.textPrimary,
              border:`1px solid ${T.borderDefault}`, opacity: loading ? .5 : 1,
              fontFamily:FONTS.sans,
            }}
          >
            <X style={{ width:14, height:14 }} /> Cancelar
          </button>
          <button
            onClick={handleConfirm} disabled={loading}
            style={{
              display:"inline-flex", alignItems:"center", gap:8,
              padding:"8px 14px", fontSize:13, fontWeight:500, borderRadius:6, cursor:"pointer",
              background:T.btnPrimaryBg, color:T.btnPrimaryText,
              border:"none", opacity: loading ? .7 : 1,
              fontFamily:FONTS.sans,
            }}
          >
            {loading
              ? <><Loader2 style={{ width:14, height:14, animation:"spin 1s linear infinite" }} /> Revelando...</>
              : <><Check style={{ width:14, height:14 }} /> Confirmar ({credits} créditos)</>
            }
          </button>
        </div>
      </div>

      <style>{`@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }`}</style>
    </div>
  )
}

// ─── BulkRevealModal — mirrors BulkRevealModal.tsx ────────────────────────
function BulkRevealModal({ isOpen, onClose, count }: { isOpen:boolean; onClose:()=>void; count:number }) {
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
    <div
      onClick={onClose}
      style={{
        position:"fixed", inset:0, zIndex:50,
        display:"flex", alignItems:"center", justifyContent:"center",
        background:"rgba(0,0,0,.6)", padding:16, fontFamily:FONTS.sans,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width:"100%", maxWidth:420, background:T.bgPrimary,
          borderRadius:12, border:`1px solid ${T.borderSubtle}`,
          boxShadow:T.shadowMd, padding:24,
          display:"flex", flexDirection:"column", gap:20,
        }}
      >
        <h2 style={{ fontSize:14, fontWeight:600, color:T.textPrimary, margin:0 }}>
          Revelar contatos de {count} candidato{count !== 1 ? "s" : ""}
        </h2>
        <p style={{ fontSize:13, color:T.textSecondary, margin:0 }}>
          Escolha o que revelar. A cobrança ocorre apenas pelos contatos efetivamente disponíveis.
        </p>

        <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
          {[
            { label:"Email", Icon:Mail, credits:2, checked:revealEmail, onChange:setRevealEmail },
            { label:"Telefone", Icon:Phone, credits:14, checked:revealPhone, onChange:setRevealPhone },
          ].map(({ label, Icon, credits, checked, onChange }) => (
            <label
              key={label}
              style={{
                display:"flex", alignItems:"center", gap:12,
                padding:"12px 14px", borderRadius:12,
                border:`1px solid ${T.borderSubtle}`,
                cursor:"pointer", background:T.bgPrimary,
              }}
            >
              <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} style={{ width:16, height:16, accentColor:T.btnPrimaryBg }} />
              <Icon style={{ width:16, height:16, color:T.textSecondary }} />
              <span style={{ flex:1, fontSize:13, color:T.textPrimary }}>{label}</span>
              <span style={{ fontSize:12, color:T.textTertiary }}>{credits} créd./candidato</span>
            </label>
          ))}
        </div>

        <div style={{ padding:16, borderRadius:12, background:T.warningBg10, border:`1px solid ${T.warningBorder30}` }}>
          <div style={{ display:"flex", gap:12, alignItems:"flex-start" }}>
            <CreditCard style={{ width:20, height:20, color:T.warning, flexShrink:0, marginTop:1 }} />
            <div>
              <p style={{ fontWeight:600, color:T.warning, fontSize:14, margin:"0 0 4px" }}>Custo máximo: {maxCredits} créditos</p>
              <p style={{ fontSize:13, color:T.warning, margin:0, opacity:.85 }}>Candidatos sem o contato escolhido não consomem créditos.</p>
            </div>
          </div>
        </div>

        <div style={{ display:"flex", justifyContent:"flex-end", gap:8 }}>
          <button onClick={onClose} disabled={loading}
            style={{ display:"inline-flex", alignItems:"center", gap:8, padding:"8px 14px", fontSize:13, fontWeight:500, borderRadius:6, cursor:"pointer", background:T.bgPrimary, color:T.textPrimary, border:`1px solid ${T.borderDefault}`, fontFamily:FONTS.sans, opacity: loading ? .5 : 1 }}>
            Cancelar
          </button>
          <button onClick={handleConfirm} disabled={loading || (!revealEmail && !revealPhone)}
            style={{ display:"inline-flex", alignItems:"center", gap:8, padding:"8px 14px", fontSize:13, fontWeight:500, borderRadius:6, cursor:"pointer", background:T.btnPrimaryBg, color:T.btnPrimaryText, border:"none", fontFamily:FONTS.sans, opacity: (loading || (!revealEmail && !revealPhone)) ? .5 : 1 }}>
            {loading ? <><Loader2 style={{ width:14, height:14, animation:"spin 1s linear infinite" }} /> Revelando…</> : `Revelar (${count})`}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Checkbox helper ──────────────────────────────────────────────────────
function CheckboxCell({ checked, indeterminate, onChange }: { checked: boolean; indeterminate?: boolean; onChange: () => void }) {
  if (checked) {
    return (
      <button onClick={e => { e.stopPropagation(); onChange() }} style={{ background:"none", border:"none", padding:0, cursor:"pointer", color:T.btnPrimaryBg, display:"flex" }}>
        <CheckSquare style={{ width:16, height:16 }} />
      </button>
    )
  }
  if (indeterminate) {
    return (
      <button onClick={e => { e.stopPropagation(); onChange() }} style={{ background:"none", border:"none", padding:0, cursor:"pointer", display:"flex" }}>
        <div style={{ width:16, height:16, borderRadius:3, border:`2px solid ${T.btnPrimaryBg}`, background:`rgba(17,24,39,.1)`, display:"flex", alignItems:"center", justifyContent:"center" }}>
          <div style={{ width:8, height:2, background:T.btnPrimaryBg, borderRadius:1 }} />
        </div>
      </button>
    )
  }
  return (
    <button onClick={e => { e.stopPropagation(); onChange() }} style={{ background:"none", border:"none", padding:0, cursor:"pointer", color:T.textDisabled, display:"flex" }}>
      <Square style={{ width:16, height:16 }} />
    </button>
  )
}

// ─── Avatar ───────────────────────────────────────────────────────────────
function Avatar({ initials }: { initials: string }) {
  return (
    <div style={{
      width:28, height:28, borderRadius:"50%",
      background:T.bgTertiary, color:T.textTertiary,
      display:"flex", alignItems:"center", justifyContent:"center",
      fontSize:10, fontWeight:600, flexShrink:0,
      fontFamily:FONTS.sans,
      border:`1px solid ${T.borderSubtle}`,
    }}>
      {initials}
    </div>
  )
}

// ─── SortIcon ─────────────────────────────────────────────────────────────
function ColHeader({ label }: { label: string }) {
  return (
    <div style={{ display:"inline-flex", alignItems:"center", gap:4, cursor:"pointer" }}>
      <span style={{ fontSize:11, fontWeight:600, color:T.textTertiary, textTransform:"uppercase", letterSpacing:.5, fontFamily:FONTS.sans }}>{label}</span>
      <ChevronUp style={{ width:12, height:12, color:T.textDisabled }} />
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────
export default function FunilBusca() {
  const [activeTab, setActiveTab] = useState("busca")
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [revealed, setRevealed] = useState<RevealedContacts>({
    c1: { email:"maria.santos.eval@email.com",  phone:"+55 11 95678-9012" },
    c2: { email:"ana.almeida24@email.com",       phone:"+55 11 92441-2559" },
    c5: { email:"bruna.moura45@email.com",       phone:"+55 11 94147-9660" },
    c6: { email:"beatriz.silva7@email.com",      phone:"+55 11 91810-8585" },
    c9: { email:"fabiana.moura9@email.com",      phone:"+55 11 93252-3127" },
    c10:{ email:"tatiana.rocha8@email.com",      phone:"+55 11 92660-4125" },
  })
  const [revealModal, setRevealModal] = useState<{ open:boolean; candidate:Candidate|null; type:"email"|"phone" }>({ open:false, candidate:null, type:"email" })
  const [bulkModal, setBulkModal] = useState(false)

  const allSelected  = selected.size === CANDIDATES.length
  const someSelected = selected.size > 0 && selected.size < CANDIDATES.length
  const toggleAll    = () => setSelected(allSelected ? new Set() : new Set(CANDIDATES.map(c => c.id)))
  const toggleOne    = (id: string) => setSelected(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n })

  const openReveal = (candidate: Candidate, type: "email"|"phone") => setRevealModal({ open:true, candidate, type })
  const confirmReveal = () => {
    if (!revealModal.candidate) return
    const c = revealModal.candidate
    const fakeEmail = `${c.name.toLowerCase().replace(/\s+/g,".")}@email.com`
    const fakePhone = `+55 11 9${Math.floor(Math.random()*8000+1000)}-${Math.floor(Math.random()*9000+1000)}`
    setRevealed(prev => ({ ...prev, [c.id]: { ...prev[c.id], [revealModal.type]: revealModal.type === "email" ? fakeEmail : fakePhone } }))
    setRevealModal({ open:false, candidate:null, type:"email" })
  }

  const TABS = [
    { id:"busca", label:"Busca" },
    { id:"favoritos", label:"Favoritos" },
    { id:"listas", label:"Listas" },
    { id:"bancos", label:"Bancos de Talentos" },
    { id:"salvas", label:"Buscas Salvas" },
    { id:"historico", label:"Histórico" },
  ]

  return (
    <div style={{ minHeight:"100vh", background:T.bgSecondary, fontFamily:FONTS.sans }}>

      {/* Import Google Fonts */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Open Sans', system-ui, sans-serif; }
        @keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
      `}</style>

      {/* ── Page header ─────────────────────────────────────────────────── */}
      <div style={{
        background:T.bgPrimary, borderBottom:`1px solid ${T.borderSubtle}`,
        padding:"14px 24px", display:"flex", alignItems:"center", justifyContent:"space-between",
      }}>
        <h1 style={{ fontSize:18, fontWeight:600, color:T.textPrimary, fontFamily:FONTS.sans }}>Funil de Talentos</h1>
        <div style={{ display:"flex", gap:8 }}>
          <button style={{
            display:"inline-flex", alignItems:"center", gap:6,
            padding:"7px 14px", fontSize:13, fontWeight:500, borderRadius:6,
            background:T.btnPrimaryBg, color:T.btnPrimaryText, border:"none", cursor:"pointer",
            fontFamily:FONTS.sans,
          }}>
            <Plus style={{ width:15, height:15 }} /> Novo Candidato
          </button>
          <button style={{
            display:"inline-flex", alignItems:"center", gap:6,
            padding:"7px 14px", fontSize:13, fontWeight:500, borderRadius:6,
            background:T.bgPrimary, color:T.textPrimary,
            border:`1px solid ${T.borderDefault}`, cursor:"pointer",
            fontFamily:FONTS.sans,
          }}>
            <Search style={{ width:15, height:15 }} /> Nova Busca
          </button>
        </div>
      </div>

      {/* ── Tab Navigation — PageTabNavigation (pill style) ─────────────── */}
      <div style={{
        background:T.bgPrimary, borderBottom:`1px solid ${T.borderSubtle}`,
        padding:"10px 24px",
      }}>
        <nav style={{
          display:"inline-flex", gap:4, padding:4,
          background:T.bgSecondary, borderRadius:8,
        }}>
          {TABS.map(tab => {
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display:"inline-flex", alignItems:"center",
                  padding:"6px 12px", borderRadius:6,
                  fontSize:12, fontWeight:500, cursor:"pointer", border:"none",
                  background: isActive ? T.bgPrimary : "transparent",
                  color: isActive ? T.textPrimary : T.textSecondary,
                  boxShadow: isActive ? T.shadowSm : "none",
                  transition:"all .15s",
                  fontFamily:FONTS.sans,
                }}
              >
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* ── Content ─────────────────────────────────────────────────────── */}
      <div style={{ padding:16, display:"flex", flexDirection:"column", gap:12 }}>

        {/* Search bar + controls row */}
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", gap:16 }}>
          {/* Left: search info */}
          <div style={{ display:"flex", alignItems:"center", gap:8 }}>
            <button style={{ padding:4, borderRadius:6, border:"none", background:"transparent", cursor:"pointer", color:T.textTertiary, display:"flex" }}>
              <ArrowLeft style={{ width:16, height:16 }} />
            </button>
            <div style={{
              display:"inline-flex", alignItems:"center", gap:6,
              background:T.bgPrimary, border:`1px solid ${T.borderSubtle}`,
              borderRadius:6, padding:"5px 10px",
            }}>
              <Search style={{ width:14, height:14, color:T.textDisabled }} />
              <span style={{ fontSize:13, fontWeight:500, color:T.textPrimary, fontFamily:FONTS.sans }}>Busca realizada</span>
              <button style={{ padding:2, border:"none", background:"transparent", cursor:"pointer", color:T.textDisabled, display:"flex", borderRadius:4 }}>
                <Edit2 style={{ width:12, height:12 }} />
              </button>
            </div>
            <button style={{ display:"inline-flex", alignItems:"center", gap:4, fontSize:13, fontWeight:500, color:T.btnPrimaryBg, background:"transparent", border:"none", cursor:"pointer", fontFamily:FONTS.sans }}>
              Editar Filtros <ChevronRight style={{ width:14, height:14 }} />
            </button>
          </div>

          {/* Right: controls */}
          <div style={{ display:"flex", gap:8 }}>
            {[
              { label:"Selecionar Todos", icon: allSelected ? <CheckSquare style={{ width:15, height:15, color:T.btnPrimaryBg }} /> : <Square style={{ width:15, height:15 }} />, onClick: toggleAll },
              { label:"Filtros", icon: <SlidersHorizontal style={{ width:15, height:15 }} /> },
            ].map(({ label, icon, onClick }) => (
              <button
                key={label}
                onClick={onClick}
                style={{
                  display:"inline-flex", alignItems:"center", gap:6,
                  padding:"6px 12px", fontSize:13, fontWeight:500, borderRadius:6,
                  background:T.bgPrimary, color:T.textPrimary,
                  border:`1px solid ${T.borderDefault}`, cursor:"pointer",
                  fontFamily:FONTS.sans,
                }}
              >
                {icon} {label}
              </button>
            ))}
            <button style={{
              display:"inline-flex", alignItems:"center", gap:6,
              padding:"6px 12px", fontSize:13, fontWeight:500, borderRadius:6,
              background:T.bgPrimary, color:T.textPrimary,
              border:`1px solid ${T.borderDefault}`, cursor:"pointer",
              fontFamily:FONTS.sans,
            }}>
              <Columns3 style={{ width:15, height:15 }} /> Colunas
              <span style={{ fontSize:11, fontWeight:600, background:T.bgTertiary, color:T.textSecondary, padding:"1px 6px", borderRadius:9999, fontFamily:FONTS.data }}>11</span>
            </button>
          </div>
        </div>

        {/* Bulk actions bar */}
        {selected.size > 0 && (
          <div style={{
            display:"flex", alignItems:"center", gap:8,
            padding:"10px 16px",
            background:"rgba(17,24,39,.04)",
            border:`1px solid rgba(17,24,39,.12)`,
            borderRadius:8,
            fontSize:13, fontWeight:500, color:T.textPrimary,
            fontFamily:FONTS.sans,
          }}>
            <span>{selected.size} candidato{selected.size !== 1 ? "s" : ""} selecionado{selected.size !== 1 ? "s" : ""}</span>
            <div style={{ flex:1 }} />
            <button
              onClick={() => setBulkModal(true)}
              style={{
                display:"inline-flex", alignItems:"center", gap:6,
                padding:"5px 12px", fontSize:12, fontWeight:500, borderRadius:6,
                background:T.btnPrimaryBg, color:T.btnPrimaryText, border:"none", cursor:"pointer",
                fontFamily:FONTS.sans,
              }}
            >
              <Mail style={{ width:14, height:14 }} /> Revelar Contatos
            </button>
            <button
              onClick={() => setSelected(new Set())}
              style={{
                display:"inline-flex", alignItems:"center", gap:6,
                padding:"5px 12px", fontSize:12, fontWeight:500, borderRadius:6,
                background:T.bgPrimary, color:T.textPrimary,
                border:`1px solid ${T.borderDefault}`, cursor:"pointer",
                fontFamily:FONTS.sans,
              }}
            >
              <X style={{ width:13, height:13 }} /> Deselecionar
            </button>
          </div>
        )}

        {/* Table */}
        <div style={{
          background:T.bgPrimary, borderRadius:12,
          border:`1px solid ${T.borderSubtle}`,
          overflow:"hidden",
          boxShadow:T.shadowSm,
        }}>
          <div style={{ overflowX:"auto" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:13 }}>
              <thead>
                <tr style={{ borderBottom:`1px solid ${T.borderSubtle}`, background:T.bgSecondary }}>
                  <th style={{ width:40, padding:"10px 12px" }}>
                    <CheckboxCell checked={allSelected} indeterminate={someSelected} onChange={toggleAll} />
                  </th>
                  <th style={{ width:32, padding:"10px 4px" }} />
                  <th style={{ width:32, padding:"10px 4px" }} />
                  <th style={{ padding:"10px 12px", textAlign:"left" }}><ColHeader label="Cargo atual" /></th>
                  <th style={{ padding:"10px 12px", textAlign:"left" }}><ColHeader label="Empresa atual" /></th>
                  <th style={{ padding:"10px 12px", textAlign:"left" }}><ColHeader label="Salário atual" /></th>
                  <th style={{ padding:"10px 12px", textAlign:"left" }}><ColHeader label="Expectativa salarial" /></th>
                  <th style={{ padding:"10px 12px", textAlign:"left", minWidth:220 }}><ColHeader label="E-mail" /></th>
                  <th style={{ padding:"10px 12px", textAlign:"left", minWidth:200 }}><ColHeader label="Celular" /></th>
                  <th style={{ padding:"10px 12px", textAlign:"left", width:60 }}>
                    <span style={{ fontSize:11, fontWeight:600, color:T.textTertiary, textTransform:"uppercase", letterSpacing:.5, fontFamily:FONTS.sans }}>LinkedIn</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {CANDIDATES.map((c, idx) => {
                  const isSelected = selected.has(c.id)
                  return (
                    <tr
                      key={c.id}
                      style={{
                        borderBottom: idx < CANDIDATES.length - 1 ? `1px solid ${T.borderSubtle}` : "none",
                        background: isSelected ? "rgba(17,24,39,.03)" : T.bgPrimary,
                        cursor:"pointer",
                      }}
                      onMouseEnter={e => !isSelected && ((e.currentTarget as HTMLElement).style.background = T.bgSecondary)}
                      onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = isSelected ? "rgba(17,24,39,.03)" : T.bgPrimary}
                    >
                      <td style={{ padding:"10px 12px" }}>
                        <CheckboxCell checked={isSelected} onChange={() => toggleOne(c.id)} />
                      </td>
                      <td style={{ padding:"10px 4px" }}>
                        <button style={{ background:"none", border:"none", padding:2, cursor:"pointer", color:T.borderDefault, display:"flex" }}>
                          <Star style={{ width:15, height:15 }} />
                        </button>
                      </td>
                      <td style={{ padding:"10px 4px" }}>
                        <button style={{ background:"none", border:"none", padding:2, cursor:"pointer", color:T.borderDefault, display:"flex" }}>
                          <Pin style={{ width:15, height:15 }} />
                        </button>
                      </td>
                      <td style={{ padding:"10px 12px" }}>
                        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                          <Avatar initials={c.initials} />
                          <div style={{ minWidth:0 }}>
                            <div style={{ fontSize:13, fontWeight:500, color:T.textPrimary, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap", fontFamily:FONTS.sans }}>{c.current_title}</div>
                            <div style={{ fontSize:11, color:T.textTertiary, fontFamily:FONTS.sans }}>{c.name}</div>
                          </div>
                        </div>
                      </td>
                      <td style={{ padding:"10px 12px" }}>
                        <span style={{ fontSize:13, color:T.textSecondary, fontFamily:FONTS.sans }}>{c.current_company}</span>
                      </td>
                      <td style={{ padding:"10px 12px" }}>
                        <span style={{ fontSize:13, color:T.textDisabled, fontFamily:FONTS.data }}>N/A</span>
                      </td>
                      <td style={{ padding:"10px 12px" }}>
                        <span style={{ fontSize:13, color:T.textDisabled, fontFamily:FONTS.data }}>N/A</span>
                      </td>
                      <td style={{ padding:"10px 12px" }}>
                        <EmailCell candidate={c} revealed={revealed} onReveal={openReveal} />
                      </td>
                      <td style={{ padding:"10px 12px" }}>
                        <PhoneCell candidate={c} revealed={revealed} onReveal={openReveal} />
                      </td>
                      <td style={{ padding:"10px 12px" }}>
                        <button style={{ display:"inline-flex", alignItems:"center", justifyContent:"center", width:28, height:28, borderRadius:6, border:"none", background:"transparent", cursor:"pointer", color:T.textDisabled }}>
                          <Linkedin style={{ width:16, height:16 }} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Footer */}
          <div style={{
            display:"flex", alignItems:"center", justifyContent:"space-between",
            padding:"10px 16px",
            borderTop:`1px solid ${T.borderSubtle}`,
            background:T.bgSecondary,
          }}>
            <span style={{ fontSize:12, color:T.textTertiary, fontFamily:FONTS.sans }}>Exibindo {CANDIDATES.length} de 127 resultados</span>
            <button style={{
              padding:"5px 12px", fontSize:12, fontWeight:500, borderRadius:6, cursor:"pointer",
              background:T.bgPrimary, color:T.textSecondary,
              border:`1px solid ${T.borderSubtle}`,
              fontFamily:FONTS.sans,
            }}>
              Carregar mais
            </button>
          </div>
        </div>

        {/* Legend */}
        <div style={{ display:"flex", alignItems:"center", gap:20, fontSize:11, color:T.textTertiary, paddingLeft:4, fontFamily:FONTS.sans, flexWrap:"wrap" }}>
          <div style={{ display:"inline-flex", alignItems:"center", gap:6 }}>
            <span style={{ display:"inline-flex", alignItems:"center", gap:4, padding:"2px 8px", borderRadius:9999, background:T.bgTertiary, color:T.textSecondary }}>
              <Mail style={{ width:11, height:11 }} /> <span style={{ fontSize:11 }}>Revelar</span>
            </span>
            <span>= e-mail disponível (2 créditos)</span>
          </div>
          <div style={{ display:"inline-flex", alignItems:"center", gap:6 }}>
            <span style={{ display:"inline-flex", alignItems:"center", gap:4, padding:"2px 8px", borderRadius:9999, background:T.successBg10, color:T.success }}>
              <Phone style={{ width:11, height:11 }} /> <span style={{ fontSize:11 }}>Revelar</span>
            </span>
            <span>= celular disponível (14 créditos)</span>
          </div>
          <div style={{ display:"inline-flex", alignItems:"center", gap:4 }}>
            <CheckCircle2 style={{ width:12, height:12, color:T.success }} />
            <span>= contato verificado</span>
          </div>
          <div style={{ display:"inline-flex", alignItems:"center", gap:4 }}>
            <AlertTriangle style={{ width:12, height:12, color:T.warning }} />
            <span>= dado com ressalva</span>
          </div>
        </div>
      </div>

      {/* Modals */}
      <RevealCreditsModal
        isOpen={revealModal.open}
        onClose={() => setRevealModal(prev => ({ ...prev, open:false }))}
        onConfirm={confirmReveal}
        revealType={revealModal.type}
        candidateName={revealModal.candidate?.name ?? ""}
      />
      <BulkRevealModal isOpen={bulkModal} onClose={() => setBulkModal(false)} count={selected.size} />
    </div>
  )
}
