"use client"

import { SearchPresetsModal, type SearchPreset, type SearchPresetsModalConfig } from "./SearchPresetsModal"

type CompanyItem = { name: string; domain?: string }

export interface CompanyPreset {
  id: string
  name: string
  description: string
  companies: CompanyItem[]
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

const toGeneric = (p: CompanyPreset): SearchPreset<CompanyItem> => ({
  id: p.id,
  name: p.name,
  description: p.description,
  items: p.companies,
  isOrganization: p.isOrganization,
})

const COMPANY_CONFIG: SearchPresetsModalConfig<CompanyItem> = {
  title: "Company Presets",
  itemLabel: "companies",
  localStorageKey: "excluded_company_custom_presets",
  generalPresets: GENERAL_PRESETS.map(toGeneric),
  parseStoredPresets: (raw: unknown[]) =>
    (raw as { id: string; name: string; companies?: CompanyItem[]; description?: string }[])
      .filter(p => Array.isArray(p.companies) && p.companies.length > 0)
      .map(p => ({
        id: p.id,
        name: p.name,
        description: p.description || `Custom preset with ${p.companies!.length} companies`,
        items: [...p.companies!],
      })),
  getPreviewText: (items: CompanyItem[]) =>
    `${items.slice(0, 2).map(c => c.name).join(', ')}, +${items.length - 2} companies`,
  generalTabSubtitle: "Presets oferecidos",
}

interface CompanyPresetsModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectPreset: (companies: CompanyItem[]) => void
  organizationPresets?: CompanyPreset[]
  onSavePreset?: (preset: { name: string; description: string; companies: CompanyItem[] }) => void
}

export function CompanyPresetsModal({
  isOpen,
  onClose,
  onSelectPreset,
  organizationPresets = [],
  onSavePreset,
}: CompanyPresetsModalProps) {
  return (
    <SearchPresetsModal<CompanyItem>
      isOpen={isOpen}
      onClose={onClose}
      onSelectPreset={onSelectPreset}
      organizationPresets={organizationPresets.map(toGeneric)}
      onSavePreset={onSavePreset ? p => onSavePreset({ ...p, companies: [] }) : undefined}
      config={COMPANY_CONFIG}
    />
  )
}

export default CompanyPresetsModal
