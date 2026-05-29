"use client"

import React, { useState, useEffect, useCallback } from "react"
import { toast } from "@/lib/toast"
import { ConfirmAlertDialog } from "@/components/agent-studio/confirm-alert-dialog"
import { useTranslations } from "next-intl"
// Sprint B QW#17 audit 2026-05-22: shadcn Tabs canonical (era <button> custom sem ARIA)
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import {
  Store, Download, Search, Star, Loader2,
  Package, CreditCard, Trash2, Check, X,
  ExternalLink, Filter, TrendingUp
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { TabSectionHeader } from "@/components/pages-agent-studio/TabSectionHeader"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
} from "@/components/ui/dialog"
// White-label canonical 2026-05-29: persona do cliente como fallback de nome
// de agente quando o billing row não traz agent_name (agente deletado etc.).
import { useAiPersona } from "@/hooks/company/use-ai-persona"

interface MarketplaceListing {
  id: string
  agent_id: string
  title: string
  short_description: string | null
  category: string
  tags: string[]
  status: string
  credits_per_execution: number
  is_free: boolean
  install_count: number
  avg_rating: number
  total_ratings: number
  agent_name: string | null
  agent_role: string | null
  agent_domain: string | null
  published_at: string | null
}

interface Installation {
  id: string
  source_agent_id: string
  installed_agent_id: string | null
  status: string
  total_executions: number
  total_credits_consumed: number
  installed_at: string | null
  agent_name: string | null
}

const CATEGORY_KEYS = ["", "sourcing", "pipeline", "analytics", "communication", "screening", "general"] as const

export default function MarketplaceTab() {
  const t = useTranslations('agents.marketplace')
  const [activeView, setActiveView] = useState<"browse" | "installed" | "billing">("browse")

  return (
    <div className="space-y-6">
      <TabSectionHeader
        title={t('title')}
        subtitle={t('subtitle')}
        icon={<Store className="w-4 h-4 text-violet-500" />}
      />

      {/* Sprint B QW#17 audit 2026-05-22: shadcn Tabs canonical (Radix com ARIA built-in) */}
      <Tabs value={activeView} onValueChange={(v) => setActiveView(v as "browse" | "installed" | "billing")}>
        <TabsList aria-label={t('viewSwitcher') || 'Visão do marketplace'}>
          <TabsTrigger value="browse" className="gap-1.5">
            <Search className="w-3.5 h-3.5" aria-hidden="true" />
            {t('browse')}
          </TabsTrigger>
          <TabsTrigger value="installed" className="gap-1.5">
            <Package className="w-3.5 h-3.5" aria-hidden="true" />
            {t('installed')}
          </TabsTrigger>
          <TabsTrigger value="billing" className="gap-1.5">
            <CreditCard className="w-3.5 h-3.5" aria-hidden="true" />
            {t('billing')}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="browse" className="mt-4">
          {/* F3 Wave F: onInstallSuccess auto-switch para tab "installed" */}
          <BrowseMarketplace onInstallSuccess={() => setActiveView("installed")} />
        </TabsContent>
        <TabsContent value="installed" className="mt-4">
          <InstalledAgents />
        </TabsContent>
        <TabsContent value="billing" className="mt-4">
          <BillingView />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function BrowseMarketplace({ onInstallSuccess }: { onInstallSuccess?: () => void }) {
  const t = useTranslations('agents.marketplace')
  const [listings, setListings] = useState<MarketplaceListing[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [category, setCategory] = useState("")
  const [search, setSearch] = useState("")
  const [installing, setInstalling] = useState<string | null>(null)

  // F4 Wave F: debounce search 300ms — evita query a cada keystroke
  const [debouncedSearch, setDebouncedSearch] = useState("")
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => { loadListings() }, [category, debouncedSearch])

  const loadListings = useCallback(async () => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      if (category) params.set("category", category)
      if (debouncedSearch) params.set("search", debouncedSearch)
      const res = await fetch(`/api/backend-proxy/agent-marketplace?${params}`)
      if (res.ok) {
        const data = await res.json()
        setListings(data.listings || [])
        setTotal(data.total || 0)
      }
    } catch (err) {
      console.error("Failed to load marketplace:", err)
    } finally {
      setIsLoading(false)
    }
  }, [category, debouncedSearch])

  // Removed: useEffect handled above with [category, search]

  const handleInstall = async (listingId: string) => {
    setInstalling(listingId)
    try {
      const res = await fetch("/api/backend-proxy/agent-marketplace/install", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ listing_id: listingId }),
      })
      if (res.ok) {
        toast.success(t('installSuccess'))
        loadListings()
        // F3 Wave F: auto-switch para tab Instalados após install com sucesso
        onInstallSuccess?.()
      } else {
        const err = await res.json().catch(() => ({ detail: t('errorGeneric') }))
        toast.error(err.detail || t('errorInstalling'))
      }
    } catch {
      toast.error(t('connectionError'))
    } finally {
      setInstalling(null)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-disabled" />
          <input
            type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder={t('searchPlaceholder') as string}
            className="w-full pl-10 pr-3 py-2 border border-lia-border-subtle rounded-lg text-sm bg-lia-bg-secondary text-lia-text-primary placeholder:text-lia-text-disabled focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/30"
          />
        </div>
        <div className="flex gap-1">
          {CATEGORY_KEYS.map(key => (
            <button
              key={key}
              onClick={() => setCategory(key)}
              className={cn(
                "px-3 py-2 rounded-lg text-xs font-medium transition-colors",
                category === key
                  ? "bg-violet-100 dark:bg-violet-950/30 text-violet-700 dark:text-violet-400"
                  : "text-lia-text-secondary hover:bg-lia-bg-tertiary"
              )}
            >
              {t(key || 'all')}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-6 h-6 animate-spin text-lia-text-disabled" aria-hidden="true" />
        </div>
      ) : listings.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 rounded-md border border-dashed border-lia-border-subtle bg-lia-bg-secondary/50">
          <Store className="w-10 h-10 text-lia-text-disabled mb-3" />
          <p className="text-sm font-medium text-lia-text-secondary">{t('noAgentsAvailable')}</p>
          <p className="text-xs text-lia-text-disabled mt-1">
            {search ? t('tryAnotherSearch') : t('noAgentsPublished')}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {listings.map(listing => (
            <div
              key={listing.id}
              className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary hover:border-violet-300 dark:hover:border-violet-700 hover:shadow-md transition-colors duration-200"
            >
              <div className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="text-sm font-semibold text-lia-text-primary" role="heading" aria-level={3}>{listing.title}</p>
                    {listing.agent_role && (
                      <p className="text-[10px] text-lia-text-secondary mt-0.5">{listing.agent_role}</p>
                    )}
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-violet-50 dark:bg-violet-950/20 text-violet-600 dark:text-violet-400">
                    {listing.category}
                  </span>
                </div>

                {listing.short_description && (
                  <p className="text-xs text-lia-text-secondary mb-3 line-clamp-2">{listing.short_description}</p>
                )}

                {listing.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {listing.tags.slice(0, 4).map((tag, i) => (
                      <span key={i} className="px-2 py-0.5 rounded text-[10px] bg-lia-bg-tertiary text-lia-text-disabled">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                <div className="flex items-center gap-4 mb-3 text-[10px] text-lia-text-secondary">
                  <span className="flex items-center gap-1">
                    <Download className="w-3 h-3" />
                    {t('installations', { count: listing.install_count })}
                  </span>
                  {listing.avg_rating > 0 && (
                    <span className="flex items-center gap-1">
                      <Star className="w-3 h-3 text-amber-400" />
                      {listing.avg_rating.toFixed(1)}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <CreditCard className="w-3 h-3" />
                    {listing.is_free ? t('free') : t('creditsPerExec', { credits: listing.credits_per_execution })}
                  </span>
                </div>

                <Button
                  size="sm"
                  onClick={() => handleInstall(listing.id)}
                  disabled={installing === listing.id}
                  className="w-full gap-2 bg-violet-600 text-white hover:bg-violet-700"
                >
                  {installing === listing.id ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
                  ) : (
                    <Download className="w-3.5 h-3.5" />
                  )}
                  {t('install')}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function InstalledAgents() {
  const t = useTranslations('agents.marketplace')
  const [installations, setInstallations] = useState<Installation[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const load = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await fetch("/api/backend-proxy/agent-marketplace/installations")
      if (res.ok) {
        const data = await res.json()
        setInstallations(data.installations || [])
      }
    } catch (err) {
      console.error("Failed to load installations:", err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  // Sprint B QW#4 audit 2026-05-22: state-driven confirm via shadcn AlertDialog
  const [uninstallTargetId, setUninstallTargetId] = useState<string | null>(null)

  const handleUninstall = (installationId: string) => {
    setUninstallTargetId(installationId)
  }

  const confirmUninstall = async () => {
    if (!uninstallTargetId) return
    try {
      await fetch(`/api/backend-proxy/agent-marketplace/installations/${uninstallTargetId}`, {
        method: "DELETE",
      })
      load()
    } catch (err) {
      console.error("Failed to uninstall:", err)
    } finally {
      setUninstallTargetId(null)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-lia-text-disabled" aria-hidden="true" />
      </div>
    )
  }

  if (installations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 rounded-md border border-dashed border-lia-border-subtle bg-lia-bg-secondary/50">
        <Package className="w-10 h-10 text-lia-text-disabled mb-3" />
        <p className="text-sm font-medium text-lia-text-secondary">{t('noInstalledAgents')}</p>
        <p className="text-xs text-lia-text-disabled mt-1">
          {t('exploreMarketplace')}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {installations.map(inst => (
        <div
          key={inst.id}
          className="flex items-center justify-between p-4 rounded-md border border-lia-border-subtle bg-lia-bg-secondary"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-violet-50 dark:bg-violet-950/20 flex items-center justify-center">
              <Package className="w-5 h-5 text-violet-500" />
            </div>
            <div>
              <p className="text-sm font-semibold text-lia-text-primary">{inst.agent_name || t('agent')}</p>
              <div className="flex items-center gap-3 mt-0.5 text-[10px] text-lia-text-secondary">
                <span>{t('executions', { count: inst.total_executions })}</span>
                <span>{t('credits', { count: inst.total_credits_consumed })}</span>
                {inst.installed_at && (
                  <span>
                    {t('installedOn', { date: new Date(inst.installed_at).toLocaleDateString() })}
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={() => handleUninstall(inst.id)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            {t('uninstall')}
          </button>
        </div>
      ))}
          {/* Sprint B QW#4 audit 2026-05-22: ConfirmAlertDialog canonical (era native confirm) */}
      <ConfirmAlertDialog
        open={uninstallTargetId !== null}
        onOpenChange={(open) => !open && setUninstallTargetId(null)}
        title={t('confirmUninstallTitle') || 'Desinstalar agente?'}
        description={t('confirmUninstall')}
        onConfirm={confirmUninstall}
        confirmLabel={t('uninstall') || 'Desinstalar'}
        destructive
      />

      </div>
  )
}

function BillingView() {
  const t = useTranslations('agents.marketplace')
  // White-label canonical 2026-05-29: fallback do nome quando agent_name
  // ausente (agente deletado fora do ciclo de billing).
  const { persona: aiPersona } = useAiPersona()
  const [billing, setBilling] = useState<Array<{
    agent_id: string
    agent_name: string
    total_executions: number
    total_credits_consumed: number
  }>>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetch("/api/backend-proxy/agent-marketplace/billing")
      .then(r => r.ok ? r.json() : [])
      .then(d => setBilling(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setIsLoading(false))
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-lia-text-disabled" aria-hidden="true" />
      </div>
    )
  }

  const totalCredits = billing.reduce((s, b) => s + b.total_credits_consumed, 0)
  const totalExecs = billing.reduce((s, b) => s + b.total_executions, 0)

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary p-4">
          <p className="text-xs text-lia-text-secondary mb-1">{t('totalCredits')}</p>
          <p className="text-2xl font-semibold text-lia-text-primary">{totalCredits.toLocaleString()}</p>
        </div>
        <div className="rounded-md border border-lia-border-subtle bg-lia-bg-secondary p-4">
          <p className="text-xs text-lia-text-secondary mb-1">{t('totalExecutions')}</p>
          <p className="text-2xl font-semibold text-lia-text-primary">{totalExecs.toLocaleString()}</p>
        </div>
      </div>

      {billing.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-8 text-lia-text-disabled">
          <TrendingUp className="w-8 h-8 mb-2" />
          <p className="text-sm">{t('noUsageRecorded')}</p>
        </div>
      ) : (
        <div className="rounded-md border border-lia-border-subtle overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-lia-bg-secondary">
                <th className="text-left px-4 py-3 text-xs font-semibold text-lia-text-secondary">{t('agentColumn')}</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-lia-text-secondary">{t('executionsColumn')}</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-lia-text-secondary">{t('creditsColumn')}</th>
              </tr>
            </thead>
            <tbody>
              {billing.map(b => (
                <tr key={b.agent_id} className="border-t border-lia-border-subtle">
                  <td className="px-4 py-3 font-medium text-lia-text-primary">{b.agent_name || aiPersona?.name || t('agent')}</td>
                  <td className="px-4 py-3 text-right text-lia-text-secondary">{b.total_executions}</td>
                  <td className="px-4 py-3 text-right font-semibold text-lia-text-primary">{b.total_credits_consumed}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
          </div>
  )
}
