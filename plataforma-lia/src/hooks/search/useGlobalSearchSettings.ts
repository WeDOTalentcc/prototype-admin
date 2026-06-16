"use client"

import { useState, useEffect, useCallback } from "react"
import { getGlobalSearchSettings, GlobalSearchSettings } from "@/lib/api/global-search-settings"

export interface GlobalSearchSettingsState {
  defaultLimit: number
  searchType: 'fast'
  showEmails: boolean
  showPhoneNumbers: boolean
  highFreshness: boolean
  autoExpandGlobal: boolean
  confirmBeforeSearch: boolean
  globalSearchEnabled: boolean
}

const defaultSettings: GlobalSearchSettingsState = {
  defaultLimit: 50,
  searchType: 'fast',
  showEmails: false,
  showPhoneNumbers: false,
  highFreshness: false,
  autoExpandGlobal: false,
  confirmBeforeSearch: true,
  globalSearchEnabled: true
}

export function useGlobalSearchSettings() {
  const [settings, setSettings] = useState<GlobalSearchSettingsState>(defaultSettings)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadSettings = useCallback(async () => {
    try {
      const data = await getGlobalSearchSettings()
      setSettings({
        defaultLimit: data.default_limit,
        searchType: data.search_type,
        showEmails: data.show_emails,
        showPhoneNumbers: data.show_phone_numbers,
        highFreshness: data.high_freshness,
        autoExpandGlobal: data.auto_expand_global,
        confirmBeforeSearch: data.confirm_before_search,
        globalSearchEnabled: data.global_search_enabled ?? true
      })
      setError(null)
    } catch (e) {
      setError('Failed to load settings')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSettings()
  }, [loadSettings])

  useEffect(() => {
    const handleSettingsUpdate = (event: CustomEvent) => {
      const detail = event.detail
      if (detail) {
        setSettings({
          defaultLimit: detail.defaultLimit ?? settings.defaultLimit,
          searchType: detail.searchType ?? settings.searchType,
          showEmails: detail.showEmails ?? settings.showEmails,
          showPhoneNumbers: detail.showPhoneNumbers ?? settings.showPhoneNumbers,
          highFreshness: detail.highFreshness ?? settings.highFreshness,
          autoExpandGlobal: detail.autoExpandGlobal ?? settings.autoExpandGlobal,
          confirmBeforeSearch: detail.confirmBeforeSearch ?? settings.confirmBeforeSearch,
          globalSearchEnabled: detail.globalSearchEnabled ?? settings.globalSearchEnabled
        })
      }
    }

    window.addEventListener('globalSearchSettingsUpdate', handleSettingsUpdate as EventListener)
    return () => {
      window.removeEventListener('globalSearchSettingsUpdate', handleSettingsUpdate as EventListener)
    }
  }, [settings])

  return {
    settings,
    loading,
    error,
    reload: loadSettings
  }
}
