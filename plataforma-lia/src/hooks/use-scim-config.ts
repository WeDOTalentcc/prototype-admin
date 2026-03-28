import { useState, useEffect } from 'react'

interface SCIMConfig {
  enabled: boolean
  directoryId: string | null
  directoryName: string | null
  directoryType: string | null
  lastSyncAt: string | null
  autoProvisionEnabled: boolean
  autoDeprovisionEnabled: boolean
}

interface UseSCIMConfigResult {
  scimConfig: SCIMConfig | null
  isLoading: boolean
  error: string | null
  isSCIMEnabled: boolean
}

export function useSCIMConfig(): UseSCIMConfigResult {
  const [scimConfig, setSCIMConfig] = useState<SCIMConfig | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchSCIMConfig = async () => {
      try {
        const response = await fetch('/api/auth/workos/session', {
          method: 'GET',
          credentials: 'include',
        })

        if (response.ok) {
          const data = await response.json()
          if (data.authenticated && data.user?.organizationId) {
            setSCIMConfig({
              enabled: true,
              directoryId: data.user.organizationId,
              directoryName: data.user.connectionType || 'Enterprise SSO',
              directoryType: data.user.connectionType,
              lastSyncAt: null,
              autoProvisionEnabled: true,
              autoDeprovisionEnabled: true,
            })
          } else {
            setSCIMConfig({
              enabled: false,
              directoryId: null,
              directoryName: null,
              directoryType: null,
              lastSyncAt: null,
              autoProvisionEnabled: false,
              autoDeprovisionEnabled: false,
            })
          }
        } else {
          setSCIMConfig({
            enabled: false,
            directoryId: null,
            directoryName: null,
            directoryType: null,
            lastSyncAt: null,
            autoProvisionEnabled: false,
            autoDeprovisionEnabled: false,
          })
        }
      } catch (err) {
        setError('Erro ao verificar configuração SCIM')
        setSCIMConfig({
          enabled: false,
          directoryId: null,
          directoryName: null,
          directoryType: null,
          lastSyncAt: null,
          autoProvisionEnabled: false,
          autoDeprovisionEnabled: false,
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchSCIMConfig()
  }, [])

  return {
    scimConfig,
    isLoading,
    error,
    isSCIMEnabled: scimConfig?.enabled ?? false,
  }
}
