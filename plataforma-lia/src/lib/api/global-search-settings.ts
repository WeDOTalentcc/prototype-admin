import { useUIPreferencesStore } from "@/stores/ui-preferences-store"
import type { StoredGlobalSearchSettings } from "@/stores/ui-preferences-store"

const API_BASE = ""

export interface GlobalSearchSettings {
  id?: string
  company_id?: string | null
  default_limit: number
  search_type: 'fast'
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
  search_type?: 'fast'
  show_emails?: boolean
  show_phone_numbers?: boolean
  high_freshness?: boolean
  auto_expand_global?: boolean
  confirm_before_search?: boolean
  global_search_enabled?: boolean
}

function saveToStore(settings: GlobalSearchSettings): void {
  try {
    useUIPreferencesStore.getState().setGlobalSearchSettingsCache({
      defaultLimit: settings.default_limit,
      searchType: settings.search_type,
      showEmails: settings.show_emails,
      showPhoneNumbers: settings.show_phone_numbers,
      highFreshness: settings.high_freshness,
      autoExpandGlobal: settings.auto_expand_global,
      confirmBeforeSearch: settings.confirm_before_search,
      globalSearchEnabled: settings.global_search_enabled
    })
  } catch (e) {
  }
}

function loadFromStore(): GlobalSearchSettings | null {
  try {
    const cached: StoredGlobalSearchSettings | null = useUIPreferencesStore.getState().globalSearchSettingsCache
    if (cached) {
      return {
        default_limit: cached.defaultLimit ?? 50,
        search_type: cached.searchType ?? 'fast',
        show_emails: cached.showEmails ?? false,
        show_phone_numbers: cached.showPhoneNumbers ?? false,
        high_freshness: cached.highFreshness ?? false,
        auto_expand_global: cached.autoExpandGlobal ?? false,
        confirm_before_search: cached.confirmBeforeSearch ?? true,
        global_search_enabled: cached.globalSearchEnabled ?? true
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
      const cachedSettings = loadFromStore()
      if (cachedSettings) {
        return cachedSettings
      }
      throw new Error(`Failed to fetch settings: ${response.status}`)
    }
    
    const settings = await response.json()
    saveToStore(settings)
    return settings
  } catch (error) {
    const cachedSettings = loadFromStore()
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
    saveToStore(settings)
    
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
