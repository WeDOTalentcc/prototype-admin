const API_BASE = process.env.NEXT_PUBLIC_API_URL || ""

// TODO: For production multi-tenancy, pass company_id from user session/auth context
// Currently uses 'demo_company' fallback in the proxy route for development

export interface GlobalSearchSettings {
  id?: string
  company_id?: string | null
  default_limit: number
  search_type: 'fast' | 'pro'
  show_emails: boolean
  show_phone_numbers: boolean
  high_freshness: boolean
  auto_expand_global: boolean
  confirm_before_search: boolean
  global_search_enabled: boolean
  created_at?: string
  updated_at?: string
}

export interface GlobalSearchSettingsUpdate {
  default_limit?: number
  search_type?: 'fast' | 'pro'
  show_emails?: boolean
  show_phone_numbers?: boolean
  high_freshness?: boolean
  auto_expand_global?: boolean
  confirm_before_search?: boolean
  global_search_enabled?: boolean
}

const STORAGE_KEY = 'globalSearchSettings'

function saveToLocalStorage(settings: GlobalSearchSettings): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      defaultLimit: settings.default_limit,
      searchType: settings.search_type,
      showEmails: settings.show_emails,
      showPhoneNumbers: settings.show_phone_numbers,
      highFreshness: settings.high_freshness,
      autoExpandGlobal: settings.auto_expand_global,
      confirmBeforeSearch: settings.confirm_before_search,
      globalSearchEnabled: settings.global_search_enabled
    }))
  } catch (e) {
  }
}

function loadFromLocalStorage(): GlobalSearchSettings | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      return {
        default_limit: parsed.defaultLimit ?? 50,
        search_type: parsed.searchType ?? 'fast',
        show_emails: parsed.showEmails ?? false,
        show_phone_numbers: parsed.showPhoneNumbers ?? false,
        high_freshness: parsed.highFreshness ?? false,
        auto_expand_global: parsed.autoExpandGlobal ?? false,
        confirm_before_search: parsed.confirmBeforeSearch ?? true,
        global_search_enabled: parsed.globalSearchEnabled ?? true
      }
    }
  } catch (e) {
  }
  return null
}

export async function getGlobalSearchSettings(): Promise<GlobalSearchSettings> {
  try {
    const response = await fetch(`${API_BASE}/api/backend-proxy/company/global-search-settings`)
    
    if (!response.ok) {
      const cachedSettings = loadFromLocalStorage()
      if (cachedSettings) {
        return cachedSettings
      }
      throw new Error(`Failed to fetch settings: ${response.status}`)
    }
    
    const settings = await response.json()
    saveToLocalStorage(settings)
    return settings
  } catch (error) {
    const cachedSettings = loadFromLocalStorage()
    if (cachedSettings) {
      return cachedSettings
    }
    return {
      default_limit: 50,
      search_type: 'fast',
      show_emails: false,
      show_phone_numbers: false,
      high_freshness: false,
      auto_expand_global: false,
      confirm_before_search: true,
      global_search_enabled: true
    }
  }
}

export async function updateGlobalSearchSettings(
  data: GlobalSearchSettingsUpdate
): Promise<GlobalSearchSettings> {
  try {
    const response = await fetch(`${API_BASE}/api/backend-proxy/company/global-search-settings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        default_limit: data.default_limit,
        search_type: data.search_type,
        show_emails: data.show_emails,
        show_phone_numbers: data.show_phone_numbers,
        high_freshness: data.high_freshness,
        auto_expand_global: data.auto_expand_global,
        confirm_before_search: data.confirm_before_search,
        global_search_enabled: data.global_search_enabled
      }),
    })

    if (!response.ok) {
      throw new Error(`Failed to update settings: ${response.status}`)
    }

    const settings = await response.json()
    saveToLocalStorage(settings)
    
    window.dispatchEvent(new CustomEvent('globalSearchSettingsUpdate', { 
      detail: {
        defaultLimit: settings.default_limit,
        searchType: settings.search_type,
        showEmails: settings.show_emails,
        showPhoneNumbers: settings.show_phone_numbers,
        highFreshness: settings.high_freshness,
        autoExpandGlobal: settings.auto_expand_global,
        confirmBeforeSearch: settings.confirm_before_search,
        globalSearchEnabled: settings.global_search_enabled
      }
    }))
    
    return settings
  } catch (error) {
    throw error
  }
}
