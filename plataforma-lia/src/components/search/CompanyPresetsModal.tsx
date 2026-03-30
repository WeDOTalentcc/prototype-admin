"use client"

import { useState, useEffect } from "react"
import { X, Search, Plus, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"

export interface CompanyPreset {
  id: string
  name: string
  description: string
  companies: { name: string; domain?: string }[]
  isOrganization?: boolean
}

const GENERAL_PRESETS: CompanyPreset[] = [
  {
    id: "b2b_startups",
    name: "B2B Startups",
    description: "Private, VC-backed companies selling products or services to other businesses",
    companies: [
      { name: "Databricks", domain: "databricks.com" },
      { name: "Stripe", domain: "stripe.com" },
      { name: "Snowflake", domain: "snowflake.com" },
      { name: "Figma", domain: "figma.com" },
      { name: "Notion", domain: "notion.so" },
      { name: "Airtable", domain: "airtable.com" },
      { name: "Miro", domain: "miro.com" },
      { name: "Monday.com", domain: "monday.com" },
      { name: "Canva", domain: "canva.com" },
      { name: "Asana", domain: "asana.com" },
      { name: "Slack", domain: "slack.com" },
      { name: "Zoom", domain: "zoom.us" },
      { name: "Twilio", domain: "twilio.com" },
      { name: "Segment", domain: "segment.com" },
      { name: "Amplitude", domain: "amplitude.com" },
      { name: "Mixpanel", domain: "mixpanel.com" },
      { name: "HubSpot", domain: "hubspot.com" },
      { name: "Intercom", domain: "intercom.com" },
      { name: "Zendesk", domain: "zendesk.com" },
      { name: "Braze", domain: "braze.com" },
    ]
  },
  {
    id: "b2c_startups",
    name: "B2C Startups",
    description: "Private, VC-backed companies selling products or services directly to consumers",
    companies: [
      { name: "Chime", domain: "chime.com" },
      { name: "Discord", domain: "discord.com" },
      { name: "Spotify", domain: "spotify.com" },
      { name: "DoorDash", domain: "doordash.com" },
      { name: "Instacart", domain: "instacart.com" },
      { name: "Robinhood", domain: "robinhood.com" },
      { name: "Coinbase", domain: "coinbase.com" },
      { name: "Plaid", domain: "plaid.com" },
      { name: "Klarna", domain: "klarna.com" },
      { name: "Revolut", domain: "revolut.com" },
      { name: "Nubank", domain: "nubank.com.br" },
      { name: "Rappi", domain: "rappi.com" },
      { name: "iFood", domain: "ifood.com.br" },
      { name: "99", domain: "99app.com" },
      { name: "QuintoAndar", domain: "quintoandar.com.br" },
      { name: "Airbnb", domain: "airbnb.com" },
      { name: "Uber", domain: "uber.com" },
      { name: "Lyft", domain: "lyft.com" },
      { name: "Pinterest", domain: "pinterest.com" },
    ]
  },
  {
    id: "cybersecurity",
    name: "Cybersecurity",
    description: "Companies protecting against digital threats and cyberattacks",
    companies: [
      { name: "CrowdStrike", domain: "crowdstrike.com" },
      { name: "Palo Alto Networks", domain: "paloaltonetworks.com" },
      { name: "Fortinet", domain: "fortinet.com" },
      { name: "Zscaler", domain: "zscaler.com" },
      { name: "Okta", domain: "okta.com" },
      { name: "SentinelOne", domain: "sentinelone.com" },
      { name: "Cloudflare", domain: "cloudflare.com" },
      { name: "Datadog", domain: "datadoghq.com" },
      { name: "Splunk", domain: "splunk.com" },
      { name: "Check Point", domain: "checkpoint.com" },
    ]
  },
  {
    id: "enterprise_saas",
    name: "Enterprise SaaS",
    description: "Companies providing cloud-based software for large organizations",
    companies: [
      { name: "Workday", domain: "workday.com" },
      { name: "ServiceNow", domain: "servicenow.com" },
      { name: "Salesforce", domain: "salesforce.com" },
      { name: "SAP", domain: "sap.com" },
      { name: "Oracle", domain: "oracle.com" },
      { name: "Adobe", domain: "adobe.com" },
      { name: "Atlassian", domain: "atlassian.com" },
      { name: "DocuSign", domain: "docusign.com" },
      { name: "Coupa", domain: "coupa.com" },
      { name: "Veeva Systems", domain: "veeva.com" },
    ]
  },
  {
    id: "fortune_50",
    name: "Fortune 50",
    description: "Top 50 companies by revenue in the Fortune 500 list",
    companies: [
      { name: "Walmart", domain: "walmart.com" },
      { name: "Amazon", domain: "amazon.com" },
      { name: "Apple", domain: "apple.com" },
      { name: "CVS Health", domain: "cvshealth.com" },
      { name: "UnitedHealth Group", domain: "unitedhealthgroup.com" },
      { name: "Exxon Mobil", domain: "exxonmobil.com" },
      { name: "Berkshire Hathaway", domain: "berkshirehathaway.com" },
      { name: "Alphabet", domain: "abc.xyz" },
      { name: "McKesson", domain: "mckesson.com" },
      { name: "Chevron", domain: "chevron.com" },
    ]
  },
  {
    id: "tech_giants",
    name: "Tech Giants (FAANG+)",
    description: "Major technology companies with global influence",
    companies: [
      { name: "Google", domain: "google.com" },
      { name: "Meta", domain: "meta.com" },
      { name: "Amazon", domain: "amazon.com" },
      { name: "Apple", domain: "apple.com" },
      { name: "Netflix", domain: "netflix.com" },
      { name: "Microsoft", domain: "microsoft.com" },
      { name: "Nvidia", domain: "nvidia.com" },
      { name: "Tesla", domain: "tesla.com" },
      { name: "OpenAI", domain: "openai.com" },
      { name: "Anthropic", domain: "anthropic.com" },
    ]
  },
  {
    id: "brazilian_unicorns",
    name: "Brazilian Unicorns",
    description: "Brazilian startups valued at $1B+ (unicórnios brasileiros)",
    companies: [
      { name: "Nubank", domain: "nubank.com.br" },
      { name: "iFood", domain: "ifood.com.br" },
      { name: "Stone", domain: "stone.com.br" },
      { name: "PicPay", domain: "picpay.com" },
      { name: "Creditas", domain: "creditas.com" },
      { name: "QuintoAndar", domain: "quintoandar.com.br" },
      { name: "Loft", domain: "loft.com.br" },
      { name: "VTEX", domain: "vtex.com" },
      { name: "Ebanx", domain: "ebanx.com" },
      { name: "Gympass", domain: "gympass.com" },
      { name: "Wildlife Studios", domain: "wildlifestudios.com" },
      { name: "Loggi", domain: "loggi.com" },
      { name: "Olist", domain: "olist.com" },
      { name: "Movile", domain: "movile.com.br" },
      { name: "MadeiraMadeira", domain: "madeiramadeira.com.br" },
    ]
  },
  {
    id: "brazilian_fintechs",
    name: "Brazilian Fintechs",
    description: "Brazilian financial technology companies",
    companies: [
      { name: "Nubank", domain: "nubank.com.br" },
      { name: "Stone", domain: "stone.com.br" },
      { name: "PicPay", domain: "picpay.com" },
      { name: "Creditas", domain: "creditas.com" },
      { name: "Ebanx", domain: "ebanx.com" },
      { name: "XP Inc", domain: "xpinc.com" },
      { name: "BTG Pactual", domain: "btgpactual.com" },
      { name: "C6 Bank", domain: "c6bank.com.br" },
      { name: "Inter", domain: "bancointer.com.br" },
      { name: "Neon", domain: "neon.com.br" },
      { name: "PagSeguro", domain: "pagseguro.uol.com.br" },
      { name: "RecargaPay", domain: "recargapay.com.br" },
    ]
  },
  {
    id: "consulting_firms",
    name: "Consulting Firms (MBB)",
    description: "Top management consulting firms",
    companies: [
      { name: "McKinsey & Company", domain: "mckinsey.com" },
      { name: "Boston Consulting Group", domain: "bcg.com" },
      { name: "Bain & Company", domain: "bain.com" },
      { name: "Accenture", domain: "accenture.com" },
      { name: "Deloitte Consulting", domain: "deloitte.com" },
      { name: "Strategy&", domain: "strategyand.pwc.com" },
      { name: "Oliver Wyman", domain: "oliverwyman.com" },
      { name: "Kearney", domain: "kearney.com" },
      { name: "Roland Berger", domain: "rolandberger.com" },
      { name: "L.E.K. Consulting", domain: "lek.com" },
    ]
  },
  {
    id: "big_4_accounting",
    name: "Big 4 Accounting",
    description: "The four largest accounting and professional services firms",
    companies: [
      { name: "Deloitte", domain: "deloitte.com" },
      { name: "PwC", domain: "pwc.com" },
      { name: "EY", domain: "ey.com" },
      { name: "KPMG", domain: "kpmg.com" },
    ]
  },
]

interface CompanyPresetsModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectPreset: (companies: { name: string; domain?: string }[]) => void
  organizationPresets?: CompanyPreset[]
  onSavePreset?: (preset: { name: string; description: string; companies: { name: string; domain?: string }[] }) => void
}

export function CompanyPresetsModal({
  isOpen,
  onClose,
  onSelectPreset,
  organizationPresets = [],
  onSavePreset
}: CompanyPresetsModalProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [activeTab, setActiveTab] = useState<"organization" | "general" | "custom">("general")
  const [showSaveForm, setShowSaveForm] = useState(false)
  const [newPresetName, setNewPresetName] = useState("")
  const [newPresetDescription, setNewPresetDescription] = useState("")
  const [customPresets, setCustomPresets] = useState<CompanyPreset[]>([])

  useEffect(() => {
    if (isOpen) {
      try {
        const stored = localStorage.getItem('excluded_company_custom_presets')
        if (stored) {
          const parsed = JSON.parse(stored)
          const formatted = parsed
            .filter((p: { companies?: { name: string; domain?: string }[] }) => Array.isArray(p.companies) && p.companies.length > 0)
            .map((p: { id: string; name: string; companies: { name: string; domain?: string }[]; description?: string }) => ({
              id: p.id,
              name: p.name,
              description: p.description || `Custom preset with ${p.companies.length} companies`,
              companies: [...p.companies]
            }))
          setCustomPresets(formatted)
        }
      } catch (e) {
      }
    }
  }, [isOpen])

  const handleDeleteCustomPreset = (presetId: string) => {
    try {
      const stored = localStorage.getItem('excluded_company_custom_presets')
      if (stored) {
        const parsed = JSON.parse(stored)
        const filtered = parsed.filter((p: { id: string }) => p.id !== presetId)
        localStorage.setItem('excluded_company_custom_presets', JSON.stringify(filtered))
        setCustomPresets(prev => prev.filter(p => p.id !== presetId))
      }
    } catch (e) {
    }
  }

  if (!isOpen) return null

  const filteredGeneralPresets = GENERAL_PRESETS.filter(
    preset => preset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              preset.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredOrgPresets = organizationPresets.filter(
    preset => preset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              preset.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredCustomPresets = customPresets.filter(
    preset => preset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              preset.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleSavePreset = () => {
    if (onSavePreset && newPresetName.trim()) {
      onSavePreset({
        name: newPresetName.trim(),
        description: newPresetDescription.trim(),
        companies: []
      })
      setNewPresetName("")
      setNewPresetDescription("")
      setShowSaveForm(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-[1px] z-overlay flex items-center justify-center p-4">
      <div className="bg-white rounded-md w-full max-w-2xl max-h-[80vh] flex flex-col dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <div className="flex items-center justify-between px-4 py-3 border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <h2 className="text-base font-semibold lia-text-800 dark:text-lia-text-primary">Company Presets</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-5 h-5 lia-text-500" />
          </button>
        </div>

        <div className="px-4 py-3 border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 lia-text-400" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search presets..."
              className="pl-9 text-sm"
            />
          </div>
        </div>

        <div className="flex border-b border-lia-border-subtle dark:border-lia-border-subtle">
          {customPresets.length > 0 && (
            <button
              onClick={() => setActiveTab("custom")}
              className={cn(
                "flex-1 px-4 py-2.5 text-sm font-medium transition-colors",
                activeTab === "custom"
                  ? "lia-text-900 dark:text-lia-text-primary border-b-2 border-gray-900 dark:border-lia-border-subtle"
                  : "lia-text-500 hover:lia-text-700 dark:text-lia-text-tertiary dark:hover:lia-text-200"
              )}
            >
              Meus Presets ({customPresets.length})
            </button>
          )}
          <button
            onClick={() => setActiveTab("organization")}
            className={cn(
              "flex-1 px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === "organization"
                ? "lia-text-900 dark:text-lia-text-primary border-b-2 border-gray-900 dark:border-lia-border-subtle"
                : "lia-text-500 hover:lia-text-700 dark:text-lia-text-tertiary dark:hover:lia-text-200"
            )}
          >
            Organization Presets
          </button>
          <button
            onClick={() => setActiveTab("general")}
            className={cn(
              "flex-1 px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === "general"
                ? "lia-text-900 dark:text-lia-text-primary border-b-2 border-gray-900 dark:border-lia-border-subtle"
                : "lia-text-500 hover:lia-text-700 dark:text-lia-text-tertiary dark:hover:lia-text-200"
            )}
          >
            General Presets ({GENERAL_PRESETS.length})
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === "custom" ? (
            <div className="space-y-4">
              <p className="text-xs lia-text-500">
                Presets que você salvou
              </p>
              
              {filteredCustomPresets.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm lia-text-500">
                    Nenhum preset salvo encontrado
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredCustomPresets.map(preset => (
                    <div
                      key={preset.id}
                      className="w-full text-left p-3 rounded-md border border-lia-border-subtle hover:border-gray-400 hover:bg-gray-50 dark:border-lia-border-default dark:hover:border-gray-500 dark:hover:bg-gray-700 transition-colors group"
                    >
                      <div className="flex items-start justify-between">
                        <button
                          onClick={() => {
                            onSelectPreset(preset.companies)
                            onClose()
                          }}
                          className="flex-1 text-left"
                        >
                          <div className="font-medium text-sm lia-text-800">
                            {preset.name}
                          </div>
                          <div className="text-xs lia-text-500 mt-0.5">
                            {preset.description}
                          </div>
                        </button>
                        <div className="flex items-center gap-2">
                          <Badge className="text-micro bg-gray-100 lia-text-600">
                            {preset.companies.length} companies
                          </Badge>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteCustomPreset(preset.id)
                            }}
                            className="p-1 opacity-0 group-hover:opacity-100 hover:bg-status-error/10 rounded-md transition-colors"
                            title="Excluir preset"
                          >
                            <Trash2 className="w-3.5 h-3.5 text-status-error" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : activeTab === "organization" ? (
            <div className="space-y-4">
              <p className="text-xs lia-text-500">
                Presets created by you and your team members
              </p>
              
              {filteredOrgPresets.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm lia-text-500 mb-4">
                    No presets found, please create a new preset
                  </p>
                  <Button
                    onClick={() => setShowSaveForm(true)}
                    className="bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Create New Preset
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredOrgPresets.map(preset => (
                    <button
                      key={preset.id}
                      onClick={() => {
                        onSelectPreset(preset.companies)
                        onClose()
                      }}
                      className="w-full text-left p-3 rounded-md border border-lia-border-subtle hover:border-gray-400 hover:bg-gray-50 dark:border-lia-border-default dark:hover:border-gray-500 dark:hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-medium text-sm lia-text-800 dark:text-lia-text-primary">
                            {preset.name}
                          </div>
                          <div className="text-xs lia-text-500 dark:text-lia-text-tertiary mt-0.5">
                            {preset.description}
                          </div>
                        </div>
                        <Badge className="text-micro bg-gray-100 lia-text-600">
                          {preset.companies.length} companies
                        </Badge>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {showSaveForm && (
                <div className="mt-4 p-4 border border-lia-border-subtle rounded-md bg-gray-50 dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
                  <h3 className="text-sm font-medium lia-text-800 mb-3">Save as Preset</h3>
                  <div className="space-y-3">
                    <div>
                      <Label className="text-xs">Preset Name</Label>
                      <Input
                        value={newPresetName}
                        onChange={(e) => setNewPresetName(e.target.value)}
                        placeholder="My Company Preset"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Description</Label>
                      <Input
                        value={newPresetDescription}
                        onChange={(e) => setNewPresetDescription(e.target.value)}
                        placeholder="Description of this preset..."
                        className="mt-1"
                      />
                    </div>
                    <div className="flex gap-2 justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowSaveForm(false)}
                      >
                        Cancel
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleSavePreset}
                        disabled={!newPresetName.trim()}
                        className="bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
                      >
                        Save Preset
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-xs lia-text-500">
                Presets oferecidos
              </p>
              
              <div className="space-y-2">
                {filteredGeneralPresets.map(preset => (
                  <button
                    key={preset.id}
                    onClick={() => {
                      onSelectPreset(preset.companies)
                      onClose()
                    }}
                    className="w-full text-left p-3 rounded-md border border-lia-border-subtle hover:border-gray-400 hover:bg-gray-50 dark:border-lia-border-default dark:hover:border-gray-500 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm lia-text-800 dark:text-lia-text-primary">
                            {preset.name}
                          </span>
                          <span className="text-xs lia-text-400">
                            ({preset.companies.slice(0, 2).map(c => c.name).join(', ')}, +{preset.companies.length - 2} companies)
                          </span>
                        </div>
                        <div className="text-xs lia-text-500 mt-0.5 line-clamp-1">
                          {preset.description}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default CompanyPresetsModal
